import gateway_helper as gwh
import logging
import os
import traceback
from dotenv import load_dotenv
from flask import Flask, request, abort, jsonify
from pathlib import Path
from xmpp_client import MUCBot


env_path = Path('.') / '.pyenv'
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.getLevelName(os.environ['XMPP_LOG_LEVEL'].upper()))

app = Flask(__name__)
for err_code in [400, 404, 415, 500]:
    app.register_error_handler(*gwh.error_handler(err_code))

known_rooms = gwh.parse_known_rooms(os.environ['KNOWN_ROOMS'])


@app.route('/post/<string:token>', methods=['POST'])
def push_send(token):
    """
    Forwarding the received JSON object to the given notification channel (identified by the token)
    Returns a JSON response along with a proper HTTP status

    :see: XMPP API docs: https://github.com/caronc/apprise/wiki/Notify_xmpp
    :see: XMPP implementation: https://github.com/caronc/apprise/blob/master/apprise/plugins/NotifyXMPP.py
    :param: token string
    :return: string, int
    """

    app.logger.info('New message received')
    app.logger.debug(request.headers)
    app.logger.debug(request.form)
    app.logger.debug(request.json)

    if token not in known_rooms.keys():
        abort(404, description='Token mismatch')

    try:
        if request.json:
            message = gwh.format_message(os.environ['MESSAGE_FORMAT'], request.json)
        else:
            message = gwh.format_message(os.environ['MESSAGE_FORMAT'], dict(request.form))
    except:
        abort(415, description='Gateway configured with unknown message format')

    try:
        xmpp = MUCBot(os.environ['JID_FROM_USER'], os.environ['JID_FROM_PASS'],
                      known_rooms[token]['room'], known_rooms[token]['nick'], message)

        if xmpp.connect(reattempt=False):
            xmpp.process(threaded=False)

        app.logger.info('Forwarded the received message as %s to %s',
                        known_rooms[token]['nick'], known_rooms[token]['room'])
    except:
        app.logger.error('Unexpected error during message processing')
        app.logger.error(traceback.format_exc())
        app.logger.error('Could not forward the message')
        app.logger.info(request.json)

        abort(500, description='Unexpected error during message processing')

    return {'success': True}, 200


if __name__ == '__main__':
    app.logger.setLevel(1)
    app.run(host='0.0.0.0')
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
