Dreambox.bundle
===============

A Plex plugin to stream live TV from your Enigma 2 based receiver to your media device.

Very quick installation instructions
====================================

( I'll write some more detailed instruction in the next update, these just cover the initial hiccups. More details can be found in the Dreambox 0.1 thread )
Put the Dreambox.bundle folder along with its contents in the plugins folder of your server and restart.

Make sure that you enter preferences via the plugin interface and do not hard-code the values as it will not work.

If using Linux (and MAC?) you will have to set the permissions of the folder to 777


Fixed in this release
=====================

Current event appearing in the middle of channel list.
    - Note that the ordering is ultimately controlled by the client, so the ordering may be not always as expected

Channels with no epg not showing.
    These now show, but again depending on the client may produce an infinite spinning wait icon.
    You also have to wait a bit more than normal for the initial load for some reason
    If you go back to the channel list the EPG will be populated and the channel will work as required.

Duration not displaying correctly.

Error on 'ZAP on channel change'.
    This option is only really required to be enabled when you have a single tuner.

Picons now work again for the channels only.
    Also loading from box rather than the resources folder. Seems to work quicker as well :).


New in this release
===================

Added support for specifying the container, video and audio codec. This is just to assist with finding out what codecs work with what client.
    If you find a new combination them please post on the forum your client and working combination and I will look at adding this permanently.

    Specifying these values only seems to set the correct client container etc. so it knows to receive a TS or MP4 stream
    rather than actually changing any transcoding settings.

    I've found that the only things I have had ro change so far is either the container to MP4 or MPEGTS, or the audio codec to MP3 or AAC

    If you set any of the values to nothing, then the default values used in the last update will be used.


Added support to specify the duration of the live stream. The transcoder will stop transcoding after the duration of the current event,
    but we may want to carry on watching after this. Note that if this is set too high then the web client may show a timeout.

Added a menu item to go straight to the current event showing on the main screen. Thanks to AK for this suggestion.

Added preference to specify the picon path on the dreambox.




If anyone has any suggestions for improvements or things i've missed please put a post on the thread for this plugin.

Ta





