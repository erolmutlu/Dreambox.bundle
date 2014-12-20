from httplib2 import ServerNotFoundError, HttpLib2Error
from socket import error
from metadata import get_thumb
import os
from enigma2 import  get_number_of_tuners, get_movie_subfolders, get_current_service, get_bouquets

ART = 'art-default.jpg'
ICON = 'icon-default.png'
LIVE = 'livetv.png'
RECORDED = 'recordedtv.png'
CLIENT = ['Plex Home Theater']
BROWSERS = ('Chrome', 'Internet Explorer', 'Opera', 'Safari')
RECEIVER_STANDBY = 0
RECEIVER_DEEP_STANDBY = 1
RECEIVER_REBOOT = 2
RECEIVER_RESTART_ENIGMA2 = 3

##################################################################
# The entry point. Sets variables and gets                       #
# the initial channel so we can reset the                        #
# box for single tuner receivers                                 #
##################################################################
def Start():
    Log('Entered Start function ')
    #TODO plugin loads default prefs, then overwrites them with ones you have saved
    #TODO if there is extra ones I reckon it knacks things up
    #TODO get stored here AppData\Local\Plex Media Server\Plug-in Support\Preferences


    Plugin.AddViewGroup('List', viewMode='InfoList', mediaType='items')
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = Locale.LocalString('Title')
    DirectoryObject.thumb = R(ICON)
    #Save the inital channel to reset the box.
    try:
        sRef, channel, provider, title, description, remaining = get_current_service(Prefs['host'], Prefs['port_web'])[0]
        Data.Save('sRef', sRef)
        Log('Loaded iniital channel from receiver')
        Data.SaveObject('Started', True)
    except (HttpLib2Error, error) as e:
        Log('Error in Start.Httplib2 error. Unable to get current service - {}'.format(e.message))
        Data.SaveObject('Started', False)
    except AttributeError as e:
        Log('Error in Start. Caught an attribute error - {}'.format(e.message))
        Data.SaveObject('Started', False)


@handler('/video/dreambox', 'Dreambox', art=ART, thumb=ICON)
def MainMenu():
    Log('Entered MainMenu function')
    items = []
    # See if we have any subfolders on the hdd
    if Data.LoadObject('Started'):
        try:
            if(Prefs['folders']):
                load_folders_from_receiver()
            items.append(on_now())
            items.append(DirectoryObject(key=Callback(Display_Bouquets),
                                   title=Locale.LocalString('Live'),
                                   thumb = R(LIVE),
                                   tagline=Locale.LocalString('LiveTag')))
            items.append(DirectoryObject(key=Callback(Display_RecordedTV),
                                   title=Locale.LocalString('Recorded'),
                                   thumb= R(RECORDED),
                                   tagline='Watch recorded content on your Enigma 2 based satellite receiver'))
            items = zap_menuitem(items)
            items.append(DirectoryObject(key=Callback(add_tools), title='Tools'))
        except (Exception, error)  as e:
            Log('Error in HTTPLib2 MainMenu. Unable to get create on_now  - {}'.format(e.message))
            # Need this entry in to make Home button work correctly
            items.append(DirectoryObject(key=Callback(MainMenu),
                                   title=Locale.LocalString('ConnectError')))
            #items.append(DirectoryObject(key=Callback(add_tools), title='Tools'))
        except AttributeError as e:
            items.append(DirectoryObject(key=Callback(MainMenu),
                                   title=Locale.LocalString('ConnectError')))
            items.append(DirectoryObject(key=Callback(add_tools), title='Tools'))

        items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
        items = check_empty_items(items)
    else:
        Log('Cannot start correctly.')
        items.append(DirectoryObject(key=Callback(MainMenu),
                                   title=Locale.LocalString('ConnectError')))
        items.append(DirectoryObject(key=Callback(add_tools), title='Tools'))
        items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
        #may want to update prefs here, so update Started value

    oc = ObjectContainer(objects=items, view_group='List', no_cache=True)
    if len(items) > 3:
        timers(oc)
    return oc


@route('/video/dreambox/thumb')
def GetThumb(series):
    locale = Locale.DefaultLocale
    if locale == 'en-us':
        locale='en'

    Log('Default locale = {}'.format(locale))

    data = get_thumb(series, locale)
    return DataObject(data, 'image/jpeg')


##################################################################
# Displays Bouquets when we have selected                        #
# Live TV from the main menu                                     #
##################################################################
@route("/video/dreambox/Display_Bouquets")
def Display_Bouquets():
    Log('Entered Display Bouquets function')

    items = []
    bouquets = get_bouquets(Prefs['host'],Prefs['port_web'])
    for bouquet in bouquets:
            items.append(DirectoryObject(key = Callback(Display_Bouquet_Channels, sender = str(bouquet[7]), index=str(bouquet[6])),
                                    title = str(bouquet[7])))
    items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    oc = ObjectContainer(objects=items, view_group='List', no_cache=True, title2=Locale.LocalString('Live'))
    return oc


##################################################################
# Displays Recorded TV when we have selected                     #
# Recorded TV from the main menu                                 #
##################################################################
@route("/video/dreambox/Display_RecordedTV")
def Display_RecordedTV(display_root=False):
    Log('Entered DisplayMovies function')

    items = []
    title2='Recorded TV'
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:
        #Do we want to view folders
        oc = ObjectContainer( view_group='List', no_cache=True, title2=title2, no_history=True)
        if Prefs['folders'] and not display_root:
            m, t = get_folders()
            Log('m is {}'.format(m))
            items.extend(m)
            oc.title2 = t
        else:
             items = add_movie_items(items)
        items = check_empty_items(items)
        oc.objects = items
        return oc


@route("/video/dreambox/Display_FolderRecordings/{dummy}")
def Display_FolderRecordings(dummy, folder=None):
    Log('Entered Display_FolderRecordings function folder={}'.format(folder))

    title2=folder
    oc = ObjectContainer( view_group='List', no_cache=True, title2=title2)
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:
        items = add_folder_items(folder)
    items = check_empty_items(items)
    oc.objects = items
    return oc



@route("/video/dreambox/Display_Bouquet_Channels/{sender}")
def Display_Bouquet_Channels(sender='', index=None):
    Log('Entered DisplayBouquetChannels function sender={} index={}'.format(sender, index))
    from enigma2 import get_channels_from_service

    items = []
    channels = get_channels_from_service(Prefs['host'], Prefs['port_web'], index, show_epg=True)

    name = sender
    Log(channels)
    for id, start, duration, current_time, title, description, sRef, name in channels:
        remaining = calculate_remaining(start, duration, current_time)
        if remaining == 0:
            remaining = None
        if description:
            name = '{}  - {}'.format(str(name), str(title))
        else:
            name = '{}'.format(str(name))
        #gets rid of na
        if name != '&lt;n/a>':
            items.append(DirectoryObject(key = Callback(Display_Channel_Events, sender=name, sRef=str(sRef), title=title),
                                    title = name,
                                    duration = remaining,
                                 thumb = picon(sRef)))
    items = check_empty_items(items)
    oc = ObjectContainer(objects=items, title2=sender, view_group='List', no_cache=True)
    Log(len(oc))
    return oc


@route("/video/dreambox/Display_Audio_Events/{sender}")
def Display_Audio_Events(sender, sRef, title=None, description=None, onnow=False):
    import time
    from enigma2 import get_audio_tracks, zap

    Log('Entered display Audio events: sender {} sref {} title {}'.format(sender, sRef, title))

    items = []
    zapped = True
    if not onnow:
        zapped = zap(Prefs['host'], Prefs['port_web'], sRef=sRef)

    if zapped:
        time.sleep(2)
        for audio_id, audio_description, active in get_audio_tracks(Prefs['host'],Prefs['port_web']):
            remaining = 0
            items.append(add_current_event(sRef=sRef, name=sender, description=description, title=title, remaining=0, audioid=audio_id, audio_description=audio_description))

    items = check_empty_items(items)
    oc = ObjectContainer(objects=items, title2='Select Audio Channel', view_group='List', no_cache=True)
    return oc


@route("/video/dreambox/Display_Channel_Events/{sender}")
def Display_Channel_Events(sender, sRef, title=None):
    Log('Entered DisplayChannelEvents function sender={} sRef={} title={}'.format(sender, sRef, title))
    import time
    from enigma2 import zap, get_number_of_audio_tracks

    items = []
    for id, start, duration, current_time, title, description, sRef, name in get_events(title, sRef):
        remaining = calculate_remaining(start, int(duration), current_time)

        if int(start) < time.time():
            result=None
            if Prefs['zap'] :#and Prefs['audio'] :
                zapped = zap(Prefs['host'],Prefs['port_web'], sRef=sRef)
                Log('Zapped is {}'.format(zapped[0]))
                if zapped[0]:
                    result = check_and_display_audio(name=name, title=title, sRef=sRef, description=description, remaining=remaining)
                else:
                    Log('Not zapped for some reason')
            else:
                items.append(add_current_event(sRef, name, title, description,
                                           remaining=remaining,
                                           piconfile=picon(sRef)))
            if title == 'N/A':
                title = 'Unknown'
            if result:
                items.append(result)

        #Add a future \ next event
        elif start > 0:
            pass
            items.append(DirectoryObject(key=Callback(AddTimer,
                                   title=title,
                                   name=name, sRef=sRef, eventid=id),
                                   title=title,
                                   duration = remaining,
                                   thumb=Callback(GetThumb, series=title)))
    items = check_empty_items(items)
    oc = ObjectContainer(objects=items, title2=sender, view_group='List', no_cache=True)
    return oc


@route("/video/dreambox/AddTimer")
def AddTimer(title='', name='', sRef='', eventid=0):
    from enigma2 import set_timer

    result = set_timer(Prefs['host'], Prefs['port_web'], sRef, eventid)
    Log('add timer result {}'.format(result))
    items=[]
    items.append(DirectoryObject(key=Callback(Display_Channel_Events, sender=name, title=title, sRef=sRef),
                                 title='Timer event added for {}.'.format(title)))
    return     ObjectContainer(objects=items, no_cache=True, replace_parent=True)


@route("/video/dreambox/Display_Timer_Events/{sender}")
def Display_Timer_Events(sender=None):
    from enigma2 import get_timers
    import datetime

    Log('Entered display timer events: sender {} '.format(sender))
    items = []
    for sRef, service_name, name, description, disabled, begin, end, duration in get_timers(Prefs['host'], Prefs['port_web'], active=True):
        dt = datetime.datetime.fromtimestamp(int(begin)).strftime('%d %b %y %H:%M')
        items.append(DirectoryObject(key=Callback(ConfirmDeleteTimer, sRef=sRef, begin=begin, end=end, servicename=service_name, name=name, sender=sender),
                                   title='{} {} ( {} ) '.format(service_name, name, dt),
                                   duration = duration * 1000,
                                   tagline = 'tagline',
                                   summary= description,
                                   thumb=picon(sRef)))
    Log('Length items {}'.format(len(items)))
    if len(items) == 0:
        items.append(DirectoryObject(key='www.google.co.uk', title=''))
    oc = ObjectContainer(objects=items, title2=sender, view_group='List', no_cache=True)
    return oc


@route("/video/dreambox/ConfirmDeletePopup")
def ConfirmDeleteTimer(sRef=None, begin=0, end=0, servicename=None, name=None, sender=None, oc=None):
    oc = ObjectContainer (no_cache=True, no_history=True)
    oc.add(DirectoryObject(key=Callback(DeleteTimer, sRef=sRef, begin=begin, end=end, servicename=servicename, name=name),
                           title="Delete {} ?".format( name)))
    oc.add(DirectoryObject(key=Callback(Display_Timer_Events, sender=sender ),title="Cancel"))
    return oc


@route("/video/dreambox/DeleteTimer")
def DeleteTimer(sRef='', begin=0, end=0, servicename='', name='', oc=None):
    Log('Entered delete timer function sRef={} begin={} end={} sn={} name={}'.format(sRef, begin, end, servicename, name))
    from enigma2 import delete_timer, get_timers

    result = delete_timer(Prefs['host'], Prefs['port_web'], sRef=sRef, begin=begin, end=end)
    Log('delete timer result {}'.format(result))
    items=[]
    oc=ObjectContainer(no_cache=True, replace_parent=True)
    if result:
        remaining_timers = get_timers(Prefs['host'], Prefs['port_web'], active=True)
        if len(remaining_timers) == 0:
            oc.add(DirectoryObject(key=Callback(MainMenu),
                                     title='Timer event deleted for {}. Click to return to main menu.'.format(name)))
        else:
            oc.add(DirectoryObject(key=Callback(Display_Timer_Events),
                                     title='Timer event deleted for {}. Click to return to active timers.'.format(name)))
    else:
        oc.add(DirectoryObject(key=Callback(Display_Timer_Events),
                                     title='Unable to delete event deleted for {}.'.format(name)))
    return oc


@route("/video/dreambox/Display_Event")
def Display_Event(sender='', channel='', description='', filename=None, subfolders=None, duration=0,
                  thumb=None, include_oc=False, rating_key=None,audioid=None, audio_description=None, includeExtras=0, includeRelated=0, includeRelatedCount=0):
    import re
    container, video_codec, audio_codec = get_codecs()
    rating_key = generate_rating_key(rating_key)
    Log('Entering Display Event sender {} channel {} desciprion {} filename {} subfolders {} duration {} '
        'includeOC {} ratingkey {}'.format(sender, channel, description, filename,
                                           subfolders, duration, include_oc, rating_key))
    recorded=False
    folder=None
    title=sender
    if filename:
        recorded=True
        if '+' in filename and include_oc == False:
            filename = filename.replace('+','zxz')
        #channel=None
        folder=sender
        Log('Subfolders is {}'.format(channel))
        if subfolders:
            Log('title in subfolders check = {}'.format(title))
            #strip the extension off
            if '.ts' not in filename:
                title=filename[:-4]
            else:
                title = re.sub('^[0-9]* [0-9]* - [a-zA-Z0-9 \+]* - ', '', filename)[:-3]
    if duration:
        duration= int(duration) #Needs to be cast to an int as it gets converted to an str when passsed in
    Log('Channel is {}'.format(channel))
    if recorded:
        channel =None
    video = MovieObject(
        key = Callback(Display_Event,
                       sender=sender,
                       channel=channel,
                       description=description,
                       duration=duration,
                       thumb=None,
                       include_oc=True,
                       rating_key=rating_key,
                       audioid=audioid,
                       filename=filename,
                       subfolders=subfolders),
        rating_key = rating_key,
        # This is what get displayedwhen the episode is displayed
        title = title,
        summary = description,
        duration = duration,
        thumb = Callback(GetThumb, series=sender),
        items = [
            MediaObject(
                container = container,
                video_codec = video_codec,
                audio_channels = 2,
                audio_codec = audio_codec,
                duration = duration,
                parts = [PartObject(key=Callback(PlayVideo, channel=channel, audioid=audioid, filename=filename, folder=folder, recorded=recorded))]
            )
        ]
    )
    if include_oc :
        oc = ObjectContainer()
        title = video.title
        video.title = re.sub('\On Now [-] *', '', title)
        if not recorded:
            #Just update this if its live
            duration = int(Prefs['duration'])*6000*10
        video.duration= duration
        oc.add(video)
        return oc
    return video


@route("video/dreambox/PlayVideo/{channel}")
def PlayVideo(channel, filename=None, folder=None, recorded=None, audioid=None, onnow=False):
    Log('Entering PlayVideo channel={} filename={} folder={} recorded={} audioid={}'.format(channel, filename, folder, recorded, audioid))
    import time
    from enigma2 import format_string, zap
    if channel:
        channel = channel.strip('.m3u8')
    if Prefs['zap'] and not recorded:
        Log('Changing Audio to {}'.format(audioid))
        zapaudio(channel, audioid)
    if recorded == 'False':
        stream = 'http://{}:{}/{}'.format(Prefs['host'], Prefs['port_video'], channel)
        Log('Stream to play {}'.format(stream))
    else:
        folder = folder.replace('\\', '/')  # required to make correct path for subfolders
        Log('channel={} filename={}'.format(format_string(folder,clean_file=True), filename))
        filename = format_string(filename, clean_file=True)
        if filename[:3] != 'hdd':
            filename= 'hdd/movie/{}/'.format(folder) + filename
        stream = 'http://{}:{}/file?file=/{}'.format(Prefs['host'], Prefs['port_web'], filename)
        Log('Recorded file  to play {}'.format(stream))

    return Redirect(stream)


@route("video/dreambox/ResetReceiver")
def ResetReceiver():
    Log('Entered ResetReceiver function')
    from enigma2 import zap
    zap, error = zap(Prefs['host'], Prefs['port_web'], Data.Load('sRef'))
    Log(error)
    if zap:
        message = 'Zapped to channel to reset receiver'
        Log(message)
    else:
        message = "Couldn't zap to channel resetting receiver"
        Log(message)
    return ObjectContainer(title2='Reset Receiver', no_cache=False, header='Reset receiver', message=message)



@route('/video/dreambox/ResetPrefs')
def ResetPrefs():
    items = []
    #Log(result)
    Data.SaveObject('Started', False)

    re = XML.ElementFromURL('http://127.0.0.1:32400/:/plugins/com.plexapp.plugins.dreambox/prefs', timeout=3)
    settings = re.xpath('//Setting')
    vals ={}
    for s in settings:
        pref =s.xpath('./@id')[0]
        vals[pref] = None
        Log(pref)
        re2 = HTTP.Request('http://127.0.0.1:32400/:/plugins/com.plexapp.plugins.dreambox/prefs/set?{}='.format(pref), timeout=5)
        re2.load()


    items.append(DirectoryObject(key=Callback(MainMenu),
                                         title='User Prefs reset. Restart plugin to load DefaultPrefs'))
    items = check_empty_items(items)
    oc = ObjectContainer(objects=items, title2='Reset user preference', no_history=True)
    return oc

@route('/video/dreambox/About')
def About():
    items = []
    items.append(DirectoryObject(key=Callback(MainMenu),
                                         title='Dreambox plugin for Plex'))
    items.append(DirectoryObject(key=Callback(MainMenu),
                                         title='Version: 02022014'))

    items = check_empty_items(items)
    oc = ObjectContainer(objects=items, title2='About', no_history=True)
    return oc

@route('/video/dreambox/SetPowerState')
def SetPowerState(state):
    from enigma2 import set_power_state
    Log('setting power state {}'.format(state))
    items = []
    title = ''
    title2 = ''
    try:
        result, error = set_power_state(Prefs['host'], Prefs['port_web'], state=state)

        if result and error == 0:
            title = 'Receiver in standby.'
            title2= 'Standby'
        if not result and error == 0:
            title = 'Receiver out of standby.'
            title2 = 'Standby'
        if result and error == 1:
            title='Receiver in deep standby.'
            title2 = 'Deep standby'
        if result and error == 2:
            title='Receiver rebooted.'
            title2 = 'Reboot receiver'
        if result and error == 3:
            title='Enigma2 restarted.'
            title2='Restart Enigma2'
        if result and error == 4:
            title='Enigma2 still restarting.'
            title2='Restarting Enigma2'
        items.append(DirectoryObject(key=Callback(MainMenu),
                                         title=title))
    except Exception as e:
        Log('Error setting powerstae {}'.format(e.message))
        title = 'Error. Return to main menu.'

    items = check_empty_items(items, title)
    oc = ObjectContainer(objects=items, title2=title2)
    return oc

@route('/video/dreambox/ResetUserPrefs')
def ResetUserPrefs():
    items = check_empty_items([])
    oc = ObjectContainer(objects=items, title2='Reset user preferences')
    return oc


##################################################
# Helpers                                        #
##################################################


def get_packets(sRef):
    import time, urllib2

    tuner = True
    Log('Entered Get Packets {}'.format(sRef))
    stream = 'http://{}:{}/{}'.format(Prefs['host'], Prefs['port_video'], str(sRef))
    Log(stream)
    streamurl = urllib2.urlopen(stream)
    bytes_to_read = 188
    for i in range(1, 100):
        packet = streamurl.read(bytes_to_read)
        if len(packet) < 188:
            tuner = False
        else:
            tuner = True
            break
    Log('Exiting Get Packets {}'.format(tuner))
    if tuner:
        return True
    return False

#################################################################
# Gets the sub folders from the receiver, if any                #
#################################################################
def load_folders_from_receiver():
    try:
        temp = Prefs['moviepath'].split(',')
        multiples = []
        for m in temp:
            multiples.append(m.rstrip(' /\\').lstrip(' /\\'))
        Log('Multiples are {}'.format(multiples))
        folders = get_movie_subfolders(Prefs['host'], path=multiples[0], folders=True)
        Log('Folders fetched from receiver {}'.format(folders))
        if len(folders) > 0:
            t = []

            for f in folders:
                s = f.lstrip(' /\\')
                Log('Check f {}'.format(f))
                if len(multiples)  > 1:
                    if s in multiples:
                        t.append(s)
                else:
                    t.append(s)
            Data.SaveObject('folders', t)
            Log('Saved subfolders from receiver {}'.format(t))
        else:
            Data.Save('folders', None)
    except os.error as e:
        Log('Error in Main Menu. Error reading movie subfolders on receiver - {}'.format(e.message))
    except HttpLib2Error as he:
        Log('Error in Main Menu. Httplib2 error - {}'.format(he.message))


##################################################################
# Gets the events from the receiver for the selected channel     #
##################################################################
def get_events(title=None, sRef=None):
    from enigma2 import get_nownext, get_fullepg, get_now
    if Prefs['fullepg']:
        events = get_fullepg(Prefs['host'], Prefs['port_web'], sRef)
    else:
        if title and title != 'N/A':
            events = get_nownext(Prefs['host'], Prefs['port_web'], sRef)
        else:
            events = get_now(Prefs['host'], Prefs['port_web'], sRef)
            Log('Get now event {}'.format(events))
    return events



##################################################################
# Adds the current event to the selected channel                 #
##################################################################
def add_current_event(sRef=None, name=None, title=None, description=None, remaining=None,
                      piconfile=None,
                      audioid=None,
                      audio_description=None):
    Log ('Entered Add Current Event {} {} {} {} {} {} audio = {} type = {}'.format(sRef, name, title, description,
                                                                                   remaining,
                                                                                   piconfile,
                                                                                   audioid,
                                                                                   audio_description))

    thumb=None
    if not audioid:
        thumb = Callback(GetThumb, series=title)
    tuner = 1
    if title == 'N/A':
        tuner = get_packets(sRef)
    if tuner:
        from metadata import get_image
        return Display_Event(sender=title,
                                     channel=sRef,
                                     description=description,
                                     duration=remaining,
                                     thumb=thumb,
                                     audioid=audioid,
                                     audio_description=audio_description)
    else:
        return check_empty_items([])


##################################################################
# Adds a menu iem for the current service .                      #
##################################################################
def on_now():
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:
        # Add a item for the current serviceon now
        result = None
        try:
            result = on_now_menuitem()
        except Exception as e:
            if e.args[0] != 'timed out':
                ResetReceiver()
                result = on_now_menuitem()
            else:
                Log('Just about to raise')
                raise
    return result

def add_tools():
    items = []
    try:
        items.append(DirectoryObject(key=Callback(SetPowerState, state = RECEIVER_STANDBY),
                                     title='Standby'))
        items.append(DirectoryObject(key=Callback(SetPowerState, state = RECEIVER_DEEP_STANDBY),
                                     title='Deep standby **cannot restart from plugin **'))
        items.append(DirectoryObject(key=Callback(SetPowerState, state = RECEIVER_REBOOT),
                                     title='Reboot receiver'))
        items.append(DirectoryObject(key=Callback(SetPowerState, state = RECEIVER_RESTART_ENIGMA2),
                                     title='Restart Enigma2'))
        items.append(DirectoryObject(key=Callback(ResetPrefs),
                                     title='Reset user preferences'))
        items.append(DirectoryObject(key=Callback(About),
                                     title='About'))
    except Exception as e:
        Log(e.message)
        items = check_empty_items(items, message='Unable to list tools.Return to main menu.')
    oc = ObjectContainer( view_group='List', no_cache=True, title2='Tools')
    oc.objects = items
    return oc



def on_now_menuitem():
    from enigma2 import get_current_service, get_number_of_audio_tracks, get_audio_tracks
    sRef, channel, provider, title, description, remaining = get_current_service(Prefs['host'], Prefs['port_web'])[0]
    if Client.Platform in CLIENT:
        result = Display_Event(sender='On Now - {}   {}'.format(channel, title), channel=sRef, description=description, duration=int(remaining*1000))
    else:
        result = Display_Event(sender='On Now - {}   {}'.format(channel, title), channel=sRef, description=description, duration=int(remaining*1000))
    return result


##################################################################
# Zaps to the chosen channel so we can get Audio                 #
##################################################################
def zapaudio( channel=None, audioid=None):
    from enigma2 import  zap, set_audio_track

    if not audioid:
        #if we have no audio id then we just zap
        zap = zap(Prefs['host'], Prefs['port_web'], channel)
        if zap:
            Log('Zapped to channel when playing video')
        else:
            Log("Couldn't zap to channel when playing video")
    else:
        #switch audio. Already zapped to get audioid, or on current channel
        zap = zap(Prefs['host'], Prefs['port_web'], channel)
        import time
        time.sleep(2)
        audio = set_audio_track(Prefs['host'], Prefs['port_web'], audioid)
        Log('Audio returned from enigma2 module {}'.format(audio))
        time.sleep(2)
        if audio:
            Log('Changed Audio to channel {}'.format(audioid))
        else:
            Log("Unable to change audio")


##################################################################
# After zapaudio, check if we have more than one audio track     #
##################################################################
def check_and_display_audio( name, title, sRef, description, remaining):
    from enigma2 import get_number_of_audio_tracks
    import time
    #this is required to allow channel to zap completley before we get the audio
    time.sleep(2)
    result=None
    #TODO Fix the audio switching/ Put a large value here so it nevr displays them
    if get_number_of_audio_tracks(Prefs['host'], Prefs['port_web']) > 10:
        # send audio data here or get it
        Log('Found 2 audio tracks')
        result = DirectoryObject(key=Callback(Display_Audio_Events,
                                                sender=name,
                                                title=title,
                                                sRef=sRef,
                                                description=description),
                               title='{}   {}'.format(name, title),
                               thumb = None,
                               summary=description,
                               duration=remaining)
    else:
        Log('Only found one audio track')
        result = add_current_event(sRef, name, title, description,
                                           remaining=remaining,
                                           piconfile=picon(sRef))
    return result


##################################################################
# Adds a menu iem for the active timers                          #
##################################################################
def timers(oc):
    from enigma2 import get_timers

    timer = get_timers(Prefs['host'], Prefs['port_web'], active=True)
    if len(timer) > 0:
        oc.add(DirectoryObject(key=Callback(Display_Timer_Events, sender='Active Timers'),
                                 title='Active timers'))


########################################################################
# Load codecs from preferences if all available                        #
# If not, load default values                                          #
########################################################################
def get_codecs():

    if Prefs['video_codec'] and Prefs['audio_codec'] and Prefs['audio_codec']:
        container = Prefs['container']
        video_codec = Prefs['video_codec']
        audio_codec = Prefs['audio_codec']
    else:
        video_codec = 'h264'
        audio_codec = 'mp3'
        container = 'mp4'
        if (Client.Platform in BROWSERS ):
            container = 'mpegts'

    return (container, video_codec, audio_codec)


########################################################################
# Generate the ratings key if required                                 #
########################################################################
def generate_rating_key(rating_key):
    import time
    if rating_key:
        return rating_key
    else:
        import uuid
        return uuid.uuid4()


########################################################################
# Calculates the remaining time of the current event                   #
########################################################################
def calculate_remaining(start=None, duration=None, current_time=None):
    if start and duration and current_time :
        if start > current_time:
            return int(duration *1000)
        if start > 0:
            return int(((start + int(duration)) - current_time) * 1000)
    else:
        return 0


########################################################################
# Returns a picon for the given channel                                #
########################################################################
def picon(sRef=None):
    Log('Entered picon function sRef={}'.format(sRef))
    if Prefs['picon'] :

        piconfile = sRef.replace(':', '_')
        piconfile = piconfile.rstrip('_')
        piconfile = piconfile + '.png'
        piconpath = 'http://{}:{}/{}/'.format(Prefs['host'], Prefs['port_web'], Prefs['piconpath'].lstrip('/').rstrip('/'))
        return '{}{}'.format(piconpath, piconfile)
    else:
        return None


########################################################################
# Adds a menu item if the receiver just has one tuner                  #
########################################################################
def zap_menuitem(items=None):
    Log('Entered zap_menuitem function items={}'.format(items))
    from enigma2 import get_number_of_tuners

    if get_number_of_tuners(Prefs['host'], Prefs['port_web']) == 1:
        items.append(DirectoryObject(key=Callback(ResetReceiver),
                               title='Reset receiver to original channel',
                               thumb = None))
    return items


#############################################################
# Adds a blank entry to the menu items if empty to stop     #
# android client crashing                                   #
#############################################################
def check_empty_items(items=[], message=None):
    #if we dont have any items, just return a blank entry. To stop Android crashing
    if not items:
        items= []
        if message:
            title = message
        else:
            title = 'No recordings found.'
        items.append(DirectoryObject(title=title, key=Callback(MainMenu)))
    return items


########################################################################
# Gets the sub folders if any for recorded TV                          #
########################################################################
def get_folders():

    folders = Data.LoadObject('folders')
    Log('Entering get_folders, loaded from data {}'.format(folders))
    items = []
    title2 = ''
    if folders:
        if Prefs['merge']:
            title2 = 'Recorded TV'
            #just produce a list of files
            # Just the root, get the subfolders as well
            items = add_movie_items(items)
            for f in folders:
                items.extend(add_folder_items(f))
        else:
            title2='Select folder'
            #create a menu level with the folders
            items.append(DirectoryObject(key=Callback(Display_RecordedTV, display_root=True),
                                   title='Root'))
            for f in folders:
                Log('Folder is {}'.format(f))
                items.append(DirectoryObject(key=Callback(Display_FolderRecordings, dummy='dummy', folder=f),
                            title=f))
    return items, title2

########################################################################
# Helper to add recorded tv items to the current items                 #
########################################################################
def add_movie_items(items=[]):
    from enigma2 import get_movies
    Log('Entering Add Movie Items')
    movies = get_movies(Prefs['host'],Prefs['port_web'])
    items = items
    for sref, title, description, channel, e2time, length, filename in movies:
        secs = length.split(':')
        duration = 0
        try:
            duration = (int(secs[0]) * 60 + int(secs[1])* 60) * 1000
        except:
            pass
        try:
            items.append(Display_Event(sender=title, filename=filename[1:],
                                         description=description, duration=duration))
        except Exception as e:
            Log('Error creating movie item  --> {}'.format(e.message))
    return items


def add_folder_items(folder=None):
    from enigma2 import get_movie_subfolders
    Log ('Entering AddFolderItems folder={}'.format(folder))
    items = []
    multiples = Prefs['moviepath'].split(',')
    result = get_movie_subfolders(host=Prefs['host'], path=multiples[0], folder_contents=folder)
    Log('Result from getmovie_subfolders {}'.format(result))
    if result:
        for f in result:

            items.append(Display_Event(sender=folder, subfolders=True, filename=f, description=None, duration=0))
    return items


