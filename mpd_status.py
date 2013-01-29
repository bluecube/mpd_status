#!/usr/bin/python

import mpd
import select
import xmpp
import time

import configuration

TAGS = {'artist': 'artist', 'title': 'title', 'album': 'source'}
NOTPLAYING = {}

class MpdConnection:
    def __init__(self, host, port, password):
        self._host = host
        self._port = port
        self._password = password

    def __enter__(self):
        print("Opening mpd connection")

        self._conn = mpd.MPDClient()
        self._conn.connect(host = self._host, port = self._port)
        if self._password is not None:
            self._conn.password(self._password)

        return self

    def __exit__(self, *args):
        print("Closing mpd connection")
        self._conn.disconnect()

    def state(self):
        return self._conn.status()['state']

    def currentsong(self):
        return self._conn.currentsong()

    def idle(self):
        self._conn.send_idle()
        select.select([self._conn], [], [])
        self._conn.fetch_idle()

class XmppTune:
    NS_TUNE = 'http://jabber.org/protocol/tune'

    def __init__(self, jid, password):
        self._jid = xmpp.protocol.JID(jid)
        self._password = password

    def __enter__(self):
        print("Opening xmpp connection")

        self._conn = xmpp.client.Client(self._jid.getDomain(), debug=[])
        self._conn.connect()
        self._conn.auth(self._jid.getNode(), self._password, self._jid.getResource())

        self._invisibility()

        self._conn.send(xmpp.protocol.Presence(priority = -128))

        return self

    def __exit__(self, *args):
        print("Closing xmpp connection")
        self._publish({})
        self._conn.disconnect()

    def _invisibility(self):
        iq = xmpp.protocol.Iq(frm = self._jid, typ = 'set')
        query = iq.addChild('query', namespace = xmpp.protocol.NS_PRIVACY)
        list_ = query.addChild('list', {'name': 'invisible'})
        item = list_.addChild('item', {'action': 'deny', 'order': 1})
        presence_out = item.addChild('presence-out')
        self._conn.send(iq)

        iq = xmpp.protocol.Iq(frm = self._jid, typ = 'set')
        query = iq.addChild('query', namespace = xmpp.protocol.NS_PRIVACY)
        active = query.addChild('active', {'name': 'invisible'})
        self._conn.send(iq)

    def _publish(self, song):
        """
        Build the xml element and send it.
        http://xmpp.org/extensions/xep-0118.html
        """
        iq = xmpp.protocol.Iq(frm = self._jid, typ = 'set')
        pubsub = iq.addChild('pubsub', namespace = xmpp.protocol.NS_PUBSUB)
        publish = pubsub.addChild('publish', {'node': self.NS_TUNE})
        item = publish.addChild('item')
        tune = item.addChild('tune', namespace = self.NS_TUNE)

        for tag, value in song.items():
            tune.addChild(tag).setData(value)

        self._conn.send(iq)
        #print(str(iq))

    def song_changed(self, song):
        """
        Handle change of active song.
        """
        if song == NOTPLAYING:
            print("Not playing")
        else:
            print("Changed to: {} - {}". format(song.get('artist', 'Unknown artist'), song.get('title', 'Unknown title')))
        self._publish({TAGS[tag]: value for (tag, value) in song.items() if tag in TAGS})

def work():
    lastsong = None
    with MpdConnection(configuration.MPD_HOST, configuration.MPD_PORT,
                       configuration.MPD_PASSWORD) as mpd_conn:
        with XmppTune(configuration.XMPP_JID,
                      configuration.XMPP_PASSWORD) as xmpp_conn:
            while True:
                if mpd_conn.state() != 'play':
                    currentsong = NOTPLAYING
                else:
                    currentsong = mpd_conn.currentsong()

                if currentsong != lastsong:
                    lastsong = currentsong
                    xmpp_conn.song_changed(currentsong)

                mpd_conn.idle()

try:
    while True:
        try:
            work()
        except IOError:
            print("Waiting {} seconds for retry".format(configuration.RETRY_TIME))
            time.sleep(configuration.RETRY_TIME)
except KeyboardInterrupt:
    print("Interrupted.")

