Dreambox.bundle
===============

A Plex plugin to stream live TV from your Enigma 2 based receiver to your media device.

Installation Instructions
====================================


Put the Dreambox.bundle folder along with its contents in the plugins folder of your server and restart.
If you download the plugin via as a ZIP from Github you will have to change the folder name from 'Dreambox.bundle-master' #
to 'Dreambox.bundle'

Make sure that you enter preferences via the plugin interface and do not hard-code the values as it will not work.

If using Linux and Mac you will have to set the permissions of the folder to 755 ( chmod -R 755 ).

There seems to be a problem when updating from certain versions. A fix has been found on the forum, around page 22 until I get chance to add it to this readme



Updates
=======

This is just a quick update mainly to try and fix the issue of the receiver locking up when you have a single tuner.

If you have one of these receivers, then a menu item will be displayed on the main menu that will ZAP back to the original channel
when you first started the plugin. when you select it.

I've also improved the 'On now' selection as this crashed when no tuners were available

Added the software version in the preferences folder.

A few updates to improve compatibility of recorded TV on web clients. Probably not working still on PHT. I'll get round to looking at PHT in more detail
at some point.




Current codec settings that seem to work for most are
=====================================================

MP4 Container(Better quality and compression than MPEGTS), H264 Video and MP3 Audio


And thanks for all the suggestions everyone. I'll try and get to look at them as I can.
