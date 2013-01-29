import getpass

MPD_HOST = 'localhost'
MPD_PORT = 6600
MPD_PASSWORD = None

XMPP_JID = 'blue.cube@njs.netlab.cz/tune'
XMPP_PASSWORD = getpass.getpass('XMPP password for {}:'.format(XMPP_JID))

RETRY_TIME = 30
