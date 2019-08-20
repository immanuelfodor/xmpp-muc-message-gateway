import logging
import os
import ssl
import traceback
from dotenv import load_dotenv
from flask import Flask, request, abort, jsonify
from json import dumps
from pathlib import Path
from xmpp_client import MUCBot


env_path = Path('.') / '.pyenv'
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.getLevelName(os.environ['XMPP_LOG_LEVEL'].upper()))

app = Flask(__name__)


def parse_known_rooms():
    """
    Parse the KNOWN_ROOMS env to a Python dictionary
    Keys are tokens, values are nested dicts of room JIDs and associated user nicks

    :return: dict
    """

    known_rooms = {}

    for pairs in os.environ['KNOWN_ROOMS'].split(' '):
        valid_token, valid_room, nick = pairs.split(':')
        known_rooms[valid_token] = {'room': valid_room, 'nick': nick}

    return known_rooms


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=str(e)), 500


@app.route('/post/<string:token>', methods=['POST'])
def push_send(token):
    """
    Forwarding the received JSON object to the given notification channel (identified by the token)
    Returns a JSON response along with a proper HTTP status

    :see: XMPP API docs: https://github.com/caronc/apprise/wiki/Notify_xmpp
    :see: XMPP implementation: https://github.com/caronc/apprise/blob/master/apprise/plugins/NotifyXMPP.py
    :param: token string
    :return: JSON, status code
    """

    app.logger.info('New message received')
    app.logger.debug(request.headers)
    app.logger.debug(request.json)

    if token not in known_rooms.keys():
        abort(404, description='Token mismatch')

    try:
        message = dumps(request.json, indent=2)
        xmpp = MUCBot(os.environ['JID_FROM_USER'], os.environ['JID_FROM_PASS'],
                      known_rooms[token]['room'], known_rooms[token]['nick'], message)
        xmpp.ssl_version = ssl.PROTOCOL_TLSv1_2

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


known_rooms = parse_known_rooms()

if __name__ == '__main__':
    app.logger.setLevel(1)
    app.run(host='0.0.0.0')
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
