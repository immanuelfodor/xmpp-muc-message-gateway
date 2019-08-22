import logging
import optparse
import ssl
import sys
import time

import sleekxmpp


class MUCBot(sleekxmpp.ClientXMPP):
    """
    Based on the SleekXMPP Mulit-User Chat (MUC) bot example

    :see: http://sleekxmpp.com/getting_started/muc.html
    """

    def __init__(self, jid, password, room, nick, message):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.add_event_handler("session_start", self.start)
        self.message = message

        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0045')  # Multi-User Chat
        self.register_plugin('xep_0199')  # XMPP Ping

        self.ssl_version = ssl.PROTOCOL_TLSv1_2

    def start(self, event):
        self.getRoster()
        self.sendPresence()

        self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)

        self.send_message(mto=self.room, mbody=self.message, mtype='groupchat')
        time.sleep(1)
        self.disconnect()


if __name__ == '__main__':
    op = optparse.OptionParser(usage='%prog [options] your message text')
    op.add_option("-j", "--jid", help="JID to use")
    op.add_option("-n", "--nick", help="MUC nickname")
    op.add_option("-p", "--password", help="password to use")
    op.add_option("-r", "--room", help="MUC room to join")
    op.add_option("-v", "--verbose", help="Verbosity to maximum", action="store_true")
    opts, args = op.parse_args()

    if None in [opts.jid, opts.nick, opts.password, opts.room] or len(args) < 1:
        op.print_help()
        sys.exit(1)

    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG)

    xmpp = MUCBot(opts.jid, opts.password, opts.room, opts.nick, " ".join(args))

    if xmpp.connect(reattempt=False):
        xmpp.process(threaded=False)
    else:
        print("connect() failed")
