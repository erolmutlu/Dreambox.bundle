Dreambox.bundle.Testing ******** May work, may not work. PLEASE USE THE MASTER FOR THE MOST STABLE VERSION.  ********
===============

A Plex plugin to stream live TV from your Enigma 2 based receiver to your media device.




Current Work
====================================

Adding support for sub folders on the hardrive, and also some partial support for episode icons .
On windows server's only at the moment, and just english bu this will be updated to get the current locale when
finished testing.


Audio support removed at the moment as it just does not want to play. This DID work though??????

Hopefully better coimpatibility with Linux servers (Missing entries fixed I think).

Also looking at why this doesnt work in Chromecast 

Installation Instructions
====================================


Put the Dreambox.bundle folder along with its contents in the plugins folder of your server and restart.
If you download the plugin via as a ZIP from Github you will have to change the folder name from 'Dreambox.bundle-master' #
to 'Dreambox.bundle'

Make sure that you enter preferences via the plugin interface and do not hard-code the values as it will not work.

If using Linux and Mac you will have to set the permissions of the folder to 755 ( chmod -R 755 ).

Preferences

The plugin stores the user preferences in the following locations:-

        Windoows - AppData\Local\Plex Media Server\Plug-in Support\Preferences

        Linux -

If you find that you are having trouble connecting to the receiver, even with the correct settings in the default preferences
then it could be that the plugin is always using the cached values. These do not get changed unless you edit them from the plugin=in interface.

In this case, delete the preferences file for the dreambox plugin, and restart the server. This will load the values in to the cache from your default preferences.

I'll look at doing this automatically at some point, so the plugin only adds new prefrences that get added, and leaves the rest of your settings alone.




