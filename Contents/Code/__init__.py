ART = 'art-default.jpg'
ICON = 'icon-default.png'
STREAM_URL = 'http://%s:%s/%s'
EPG_URL = 'http://%s:%s/web/epgnow?bRef=%s'
LIVE = 'livetv.png'
RECORDED = 'recordedtv.png'
CLIENT = ['Plex Home Theater']
BROWSERS = ('Chrome', 'Internet Explorer', 'Opera', 'Safari')


def Start():
    Log('Entered Start function ')
    from enigma2 import get_current_service
    Plugin.AddViewGroup('List', viewMode='InfoList', mediaType='items')
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = Locale.LocalString('Title')
    DirectoryObject.thumb = R(ICON)
    #Save the inital channel to reset the box
    try:
        sRef, channel, provider, title, description, remaining = get_current_service(Prefs['host'], Prefs['port_web'])[0]
        Data.Save('sRef', sRef)
    except:
        Log('Error in Start. Unable to get current service - {}'.format(e.reason))



@handler('/video/dreambox', 'Dreambox', art=ART, thumb=ICON)
def MainMenu():
    Log('Entered MainMenu function')
    from enigma2 import  get_number_of_tuners
    items = []
    try:
        items.append(on_now())
        items.append(DirectoryObject(key=Callback(Display_Bouquets),
                               title=Locale.LocalString('Live'),
                               thumb = R(LIVE),
                               tagline=Locale.LocalString('LiveTag')))
        items.append(DirectoryObject(key=Callback(Display_Movies),
                               title=Locale.LocalString('Recorded'),
                               thumb= R(RECORDED),
                               tagline='Watch recorded content on your Enigma 2 based satellite receiver'))
        items = zap_menuitem(items)
    except Exception as e:
        Log('Error in MainMenu. Unable to get create on_now  - {}'.format(e))
        # Need this entry in to make Home button work correctly
        items.append(DirectoryObject(key='http://www.google.com',
                               title=Locale.LocalString('ConnectError')))

    items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    oc = ObjectContainer(objects=items, view_group='List', no_cache=True)
    if len(items) > 2:
        timers(oc)
    return oc

@route("/video/dreambox/Display_Bouquets")
def Display_Bouquets():
    Log('Entered Display Bouquets function')
    from enigma2 import get_bouquets

    items = []
    bouquets = get_bouquets(Prefs['host'],Prefs['port_web'])
    for bouquet in bouquets:
            items.append(DirectoryObject(key = Callback(Display_Bouquet_Channels, sender = str(bouquet[7]), index=str(bouquet[6])),
                                    title = str(bouquet[7])))
    items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    oc = ObjectContainer(objects=items, view_group='List', no_cache=True, title2=Locale.LocalString('Live'))
    return oc

@route("/video/dreambox/Display_Movies")
def Display_Movies():
    Log('Entered DisplayMovies function')
    from enigma2 import get_movies

    items = []
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:

        movies = get_movies(Prefs['host'],Prefs['port_web'])
        Log(movies)
        for sref, title, description, channel, e2time, length, filename in movies:
            items.append(Display_Movie_Event(sender=title, filename=filename[1:], description=description, duration=int(100000)))
        items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
        oc = ObjectContainer(objects=items, view_group='List', no_cache=True, title2='Recorded TV')
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
    items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    oc = ObjectContainer(objects=items, title2=sender, view_group='List', no_cache=True)
    Log(len(oc))
    return oc




@route("/video/dreambox/Display_Channel_Events/{sender}")
def Display_Channel_Events(sender, sRef, title=None):
    Log('Entered DisplayChannelEvents function sender={} sRef={} title={}'.format(sender, sRef, title))
    import time
    from enigma2 import zap, get_number_of_audio_tracks

    items = []
    for id, start, duration, current_time, title, description, sRef, name in get_events(title, sRef):
        remaining = calculate_remaining(start, int(duration), current_time)
        #Add current event
        #work
        result=None
        if int(start) < time.time():
            result=None
            if Prefs['zap'] and Prefs['audio'] :
                zapped = zap(Prefs['host'],Prefs['port_web'], sRef=sRef)
                Log('Zapped is {}'.format(zapped[0]))
                if zapped[0]:
                    import time
                    time.sleep(0.250)
                    if get_number_of_audio_tracks(Prefs['host'], Prefs['port_web']) > 1:
                        # send audio data here or get it
                        result = DirectoryObject(key=Callback(Display_Audio_Events,
                                                              sender=name,
                                                              title=title,
                                                              sRef=sRef,
                                                              description=description),
                               title='{}   {}'.format(name, title),
                               thumb = picon(sRef),
                               summary=description,
                               duration=remaining)
                    else:
                        Log('Only found one audio track')
                else:
                    Log('Not zapped for some reason')
            if not result:
                result = add_current_event(sRef, name, title, description,
                                           remaining=remaining,
                                           piconfile=picon(sRef))
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
                                   thumb=picon(sRef)))
    items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    oc = ObjectContainer(objects=items, title2=sender, view_group='List', no_cache=True, no_history=True)
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
    return     oc



@route("/video/dreambox/Display_Movie_Event/hdd/movie")
def Display_Movie_Event(sender=None, filename=None, description=None, duration=None, thumb=R(ICON), include_oc=False, rating_key=None):
    Log('Entered movie event {} {} {} {} {} {} {}'.format(sender, filename, description, duration, thumb, include_oc, rating_key))
    from enigma2 import format_string
    container, video_codec, audio_codec = get_codecs()
    rating_key = generate_rating_key(rating_key)
    video = EpisodeObject(
        key = Callback(Display_Movie_Event, sender=sender, filename=filename, description=description, duration=duration , thumb=thumb, include_oc=True, rating_key=rating_key),
        rating_key=rating_key,
        title=sender,
        summary=description,
        thumb=picon(sender),
        items=[
            MediaObject(
                container = container,
                video_codec = video_codec,
                audio_codec = audio_codec,
                audio_channels = 2,
                parts = [PartObject(key=Callback(PlayVideo, channel='sender', filename=filename, recorded=True))]
            )
        ]
    )
    if include_oc:
        oc = ObjectContainer()
        oc.add(video)
        return oc
    import re
    video.title= re.sub('\On Now [-] *', '', video.title)
    return video


@route("/video/dreambox/Display_Event")
def Display_Event(sender='', channel='', description='', duration=0, thumb=None, include_oc=False, rating_key=None, audioid=None, audiotype=None):
    container, video_codec, audio_codec = get_codecs()
    rating_key = generate_rating_key(rating_key)
    Log('Entering Display Event {}'.format(channel))
    if not audiotype:
        # This takes into account the return callback.
        audiotype= sender
        if duration:
            duration= int(duration) #Needs to be cast to an int as it gets converted to an str when passsed in
    video = EpisodeObject(
        key = Callback(Display_Event,
                       sender=sender,
                       channel=channel,
                       description=description,
                       duration=duration,
                       thumb=R(ICON),
                       include_oc=True,
                       rating_key=rating_key,
                       audioid=audioid),
        rating_key = rating_key,
        title = audiotype,
        summary = description,
        duration = duration,
        thumb = picon(channel),
        items = [
            MediaObject(
                container = container,
                video_codec = video_codec,
                audio_channels = 2,
                audio_codec = audio_codec,
                parts = [PartObject(key=Callback(PlayVideo, channel=channel, audioid=audioid))]
            )
        ]
    )
    if include_oc:
        import re
        oc = ObjectContainer()
        title = video.title
        video.title = re.sub('\On Now [-] *', '', title)
        duration = int(Prefs['duration'])*6000*10
        video.duration= duration
        oc.add(video)
        return oc
    return video


@route("video/dreambox/PlayVideo/{channel}")
def PlayVideo(channel, filename=None,  recorded=False, audioid=None):
    import urllib2, time
    from enigma2 import format_string, zap
    #TODO Id audio here we have already zapped, just set the audio
    channel = channel.strip('.m3u8')
    if Prefs['zap'] and not recorded:
        zapaudio(channel, audioid)
    if not recorded:
        stream = 'http://{}:{}/{}'.format(Prefs['host'], Prefs['port_video'], channel)
        Log('Stream to play {}'.format(stream))
    else:
        filename = format_string(filename, clean_file=True)
        stream = 'http://{}:{}/file?file=/{}'.format(Prefs['host'], Prefs['port_web'], filename)
        Log('Recorded file  to play {}'.format(stream))
    return Redirect(stream)


#Zap to audio
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
        audio = set_audio_track(Prefs['host'], Prefs['port_web'], audioid)
        if audio:
            Log('Changed Audio to channel {}'.format(audioid))
        else:
            Log("Unable to change audio")



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
                      audiotype=None):
    # now check if we need to use the service
    Log ('Entered Add Current Event {} {} {} {} {} {} audio = {} type = {}'.format(sRef, name, title, description,
                                                                                   remaining,
                                                                                   piconfile,
                                                                                   audioid,
                                                                                   audiotype))
    if Client.Platform in CLIENT:
        return VideoClipObject(url='http://{}/{}/{}/{}'.format(Prefs['host'], Prefs['port_web'], Prefs['port_video'], sRef),
                               title='{}  - {}'.format(name, title),
                               summary=description,
                               thumb=picon(sRef))
    else:
        tuner = 1
        if title == 'N/A':
            tuner = get_packets(sRef)
        if tuner:
            return Display_Event(sender=title,
                                 channel=sRef,
                                 description=description,
                                 duration=remaining,
                                 thumb=picon(sRef),
                                 audioid=audioid,
                                 audiotype=audiotype)
        else:
            return None


##################################################################
# Adds a menu iem for the current service                        #
##################################################################
def on_now():
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:
        # Add a item for the current serviceon now
        result = None
        try:
            result = on_now_menuitem()
        except:
            #if we get here then there's no free tuners, so issue a zap.
            #What do we zap to if there's no tuners when we start?
            ResetReceiver()
            result = on_now_menuitem()
    return result


def on_now_menuitem():
    from enigma2 import get_current_service, get_number_of_audio_tracks, get_audio_tracks
    sRef, channel, provider, title, description, remaining = get_current_service(Prefs['host'], Prefs['port_web'])[0]
    if Client.Platform in CLIENT:
        result = VideoClipObject(url='http://{}/{}/{}/{}'.format(Prefs['host'], Prefs['port_web'], Prefs['port_video'], sRef),
                                               title='On Now - {}   {}'.format(channel, description))
    else:
        if Prefs['zap'] and Prefs['audio'] and (get_number_of_audio_tracks(Prefs['host'], Prefs['port_web']) > 1):

            result = DirectoryObject(key=Callback(Display_Audio_Events, sender=channel, title=title, sRef=sRef, description=description, onnow=True),
                               title='On Now - {}   {}'.format(channel, title),
                               thumb = picon(sRef),
                               summary=description,
                               duration=int(remaining*1000),
                               tagline='Current chnnel')
        else:
            #Just present the usual link directly to the
            result = Display_Event(sender='On Now - {}   {}'.format(channel, title), channel=sRef, description=description, duration=int(remaining*1000))
    return result

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

        for audio_id, audio_description, active in get_audio_tracks(Prefs['host'],Prefs['port_web']):
            remaining = 0
            items.append(add_current_event(sRef=sRef, name=sender, description=description, title=title, remaining=0, audioid=audio_id, audiotype=audio_description))

        items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    oc = ObjectContainer(objects=items, title2='Select Audio Channel', view_group='List', no_cache=True)
    return oc


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
        time.sleep(0.00001)
        return time.clock()

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