#!/usr/bin/python

import mpd
import select
import xmpp

import configuration

TAGS = {'artist': 'artist', 'title': 'title', 'album': 'source'}
NOTPLAYING = {}
NS_TUNE = 'http://jabber.org/protocol/tune'

def invisibility():
    iq = xmpp.protocol.Iq(frm = jid, typ = 'set')
    query = iq.addChild('query', namespace = xmpp.protocol.NS_PRIVACY)
    list_ = query.addChild('list', {'name': 'invisible'})
    item = list_.addChild('item', {'action': 'deny', 'order': 1})
    presence_out = item.addChild('presence-out')
    jabber.send(iq)

    iq = xmpp.protocol.Iq(frm = jid, typ = 'set')
    query = iq.addChild('query', namespace = xmpp.protocol.NS_PRIVACY)
    active = query.addChild('active', {'name': 'invisible'})
    jabber.send(iq)

def publish(song):
    """
    Build the xml element and send it.
    http://xmpp.org/extensions/xep-0118.html
    """
    iq = xmpp.protocol.Iq(frm = jid, typ = 'set')
    pubsub = iq.addChild('pubsub', namespace = xmpp.protocol.NS_PUBSUB)
    publish = pubsub.addChild('publish', {'node': NS_TUNE})
    item = publish.addChild('item')
    tune = item.addChild('tune', namespace = NS_TUNE)

    for tag, value in song.items():
        tune.addChild(tag).setData(value)

    jabber.send(iq)
    #print(str(iq))

def song_changed(song):
    """
    Handle change of active song.
    """
    if song == NOTPLAYING:
        print("Not playing")
    else:
        print("Changed to: {} - {}". format(song.get('artist', 'Unknown artist'), song.get('title', 'Unknown title')))
    publish({TAGS[tag]: value for (tag, value) in song.items() if tag in TAGS})

def not_playing():
    """
    Disable tune publishing.
    """
    song_changed(NOTPLAYING)


print("Opening mpd connection")

music = mpd.MPDClient()
music.connect(host = configuration.MPD_HOST, port = configuration.MPD_PORT)
if configuration.MPD_PASSWORD is not None:
    music.password(configuration.MPD_PASSWORD)

print("Opening xmpp connection")

jid = xmpp.protocol.JID(configuration.XMPP_JID)
jabber = xmpp.client.Client(jid.getDomain(), debug=[])
jabber.connect()
jabber.auth(jid.getNode(), configuration.XMPP_PASSWORD, jid.getResource())

invisibility()

jabber.send(xmpp.protocol.Presence(priority = -128))

print("Running")

try:
    lastsong = {}
    while True:
        if music.status()['state'] != 'play':
            currentsong = NOTPLAYING
        else:
            currentsong = music.currentsong()

        if currentsong != lastsong:
            lastsong = currentsong
            song_changed(currentsong)
        
        music.send_idle()
        select.select([music], [], [])
        music.fetch_idle()
except KeyboardInterrupt:
    print("Interrupted.")
finally:
    not_playing()

    music.disconnect()
    jabber.disconnect()

