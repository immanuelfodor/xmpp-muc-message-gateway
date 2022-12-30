import logging
import optparse
import ssl
import sys
import time

import slixmpp


class MUCBot(slixmpp.ClientXMPP):
    """
    Based on the SliXMPP Mulit-User Chat (MUC) bot example

    :see: https://slixmpp.readthedocs.io/getting_started/muc.html
    :see: https://github.com/poezio/slixmpp/blob/master/docs/getting_started/muc.rst
    """

    def __init__(self, jid, password, room, nick, message):
        slixmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.add_event_handler("session_start", self.start)
        self.message = message

        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0045')  # Multi-User Chat
        self.register_plugin('xep_0199')  # XMPP Ping

        self.ssl_version = ssl.PROTOCOL_TLSv1_2

    def start(self, event):
        self.get_roster()
        self.send_presence()

        # TODO: join_muc has been refactored in upstream since the creation of the gateway,
        #   so instead of the original `wait=True`, we might need to use the new 
        #   `join_muc_wait` function in the future if the wait is necessary.
        #   @see: https://github.com/immanuelfodor/xmpp-muc-message-gateway/issues/3
        self.plugin['xep_0045'].join_muc(self.room, self.nick)

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
    xmpp.connect()
    xmpp.process(forever=False)
