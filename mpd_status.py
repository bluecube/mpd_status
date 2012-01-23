#!/usr/bin/python

import mpd
import select
import xmpp
from xmpp import simplexml
from pprint import pprint

import configuration

TAGS = {'artist': 'artist', 'title': 'title', 'album': 'source'}

def publish(song):
    global msg_counter

    iq = xmpp.protocol.Iq(frm=jid, typ='set')
    pubsub = iq.addChild('pubsub', namespace = 'http://jabber.org/protocol/pubsub')
    publish = pubsub.addChild('publish', {'node': 'http://jabber.org/protocol/tune'})
    item = publish.addChild('item')
    tune = item.addChild('tune', namespace = 'http://jabber.org/protocol/tune')

    for tag, value in song.items():
        tune.addChild(tag).setData(value)

    jabber.send(iq)
    #print(str(iq))

def publish_song(song):
    print("Changed to: {} - {}". format(song['artist'], song['title']))
    publish({TAGS[tag]: value for (tag, value) in song.items() if tag in TAGS})

def not_playing():
    print("Not playing")
    publish({})


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
jabber.sendInitPresence(requestRoster = 0)

print("Running")

msg_counter = 0

try:
    lastsong = None
    while True:
        if music.status()['state'] != 'play':
            not_playing()
            lastsong = None
        else:
            currentsong = music.currentsong()
            if currentsong != lastsong:
                lastsong = currentsong
                publish_song(currentsong)
        
        music.send_idle()
        select.select([music], [], [])
        music.fetch_idle()
except KeyboardInterrupt:
    print("Interrupted.")
finally:
    not_playing()

    music.disconnect()
    jabber.disconnect()

