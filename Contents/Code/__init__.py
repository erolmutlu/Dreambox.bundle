ART = 'art-default.jpg'
ICON = 'icon-default.png'
STREAM_URL = 'http://%s:%s/%s'
EPG_URL = 'http://%s:%s/web/epgnow?bRef=%s'
LIVE = 'livetv.png'
RECORDED = 'recordedtv.png'
CLIENT = ['Plex Home Theater']
BROWSERS = ('Chrome', 'Internet Explorer', 'Opera', 'Safari')



def Start():
    from enigma2 import get_current_service
    Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = 'Dreambox'
    DirectoryObject.thumb = R(ICON)
    Resource.AddMimeType('image/png','png')
    #Save the inital channel to reset the box
    sRef, channel, provider, title, description, remaining = get_current_service(Prefs['host'], Prefs['port_web'])[0]
    Data.Save('sRef', sRef)



@handler('/video/dreambox', 'Dreambox', art=ART, thumb=ICON)
def MainMenu():
    from enigma2 import  get_number_of_tuners
    items = []
    items.append(on_now())
    items.append(DirectoryObject(key=Callback(Display_Bouquets),
                               title='Live TV',
                               thumb = R(LIVE),
                               tagline='Watch live TV direct from your Enigma 2 based satellite receiver'))
    items.append(DirectoryObject(key=Callback(Display_Movies),
                               title='Recorded TV',
                               thumb= R(RECORDED),
                               tagline='Watch recorded content on your Enigma 2 based satellite receiver'))
    items = zap_menuitem(items)
    items.append(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    oc = ObjectContainer(objects=items, view_group='List', no_cache=False)
    timers(oc)
    return oc


@route("/video/dreambox/Display_Bouquets")
def Display_Bouquets():
    from enigma2 import get_bouquets

    items = []
    bouquets = get_bouquets(Prefs['host'],Prefs['port_web'])
    for bouquet in bouquets:
            items.append(DirectoryObject(key = Callback(Display_Bouquet_Channels, sender = str(bouquet[7]), index=str(bouquet[6])),
                                    title = str(bouquet[7])))
    oc = ObjectContainer(objects=items, view_group='List', no_cache=False, title1='Dreambox', title2='Live TV')
    return oc


@route("/video/dreambox/Display_Movies")
def Display_Movies():
    from enigma2 import get_movies

    oc = ObjectContainer(view_group='List', no_cache=True, title2='Recorded TV')
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:

        movies = get_movies(Prefs['host'],Prefs['port_web'])
        Log(movies)
        for sref, title, description, channel, e2time, length, filename in movies:
            oc.add(Display_Movie_Event(sender=title, filename=filename[1:], description=description, duration=int(100000)))
        return oc

@route("/video/dreambox/Display_Bouquet_Channels/{name}")
def Display_Bouquet_Channels(sender, index):
    from enigma2 import get_channels_from_service

    items = []
    channels = get_channels_from_service(Prefs['host'], Prefs['port_web'], index, show_epg=True)
    name = sender
    oc = ObjectContainer(title1=name, title2='Live TV', view_group='List', no_cache=True)
    Log(channels)
    for id, start, duration, current_time, title, description, sRef, name in channels:
        remaining = calculate_remaining(start, duration, current_time)
        if description:
            name = '{}  - {}'.format(str(name), str(title))
        else:
            name = '{}'.format(str(name))
        #gets rid of na
        if name != '&lt;n/a>':
            Log('remaining {}'.format(name))
            oc.add(DirectoryObject(key = Callback(Display_Channel_Events, sender=name, sRef=str(sRef), title=title),
                                    title = name,
                                    duration = remaining,
                                    thumb = picon(sRef)))

    return oc




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





@route("/video/dreambox/Display_Channel_Events/{sender}")
def Display_Channel_Events(sender, sRef, title=None):
    import time

    Log('Entered display channel events: sender {} sref {} title {}'.format(sender, sRef, title))
    items = []
    for id, start, duration, current_time, title, description, sRef, name in get_events(title, sRef):
        remaining = calculate_remaining(start, int(duration), current_time)
        #Add current event

        if int(start) < time.time():
            result = add_current_event(sRef, name, title, description, remaining, picon(sRef))
            if title == 'N/A':
                title = 'Unknown'
            if result:
                items.append(result)
        #Add a future \ next event
        elif start > 0:
            items.append(DirectoryObject(key=Callback(TimerPopup,
                                   title='Timer',
                                   message='Timer created for \n\n{} {} *** Not working yet ***'.format(name, title)),
                                   title=title,
                                   duration = remaining,
                                   thumb=picon(sRef),
                                   summary='Click here to search for stuff'))

        oc = ObjectContainer(objects=items, title2=sender, view_group='List', no_cache=True)
    return oc



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

##11111##################################################################################################
@route("/video/dreambox/Display_Event")
def Display_Event(sender, channel, description, duration, thumb=None, include_oc=False, rating_key=None):
    container, video_codec, audio_codec = get_codecs()
    rating_key = generate_rating_key(rating_key)
    Log('Entering Display Event {}'.format(channel))

    video = EpisodeObject(
        key = Callback(Display_Event, sender=sender, channel=channel, description=description, duration=duration, thumb=R(ICON), include_oc=True, rating_key=rating_key),
        rating_key = rating_key,
        title = sender,
        summary = description,
        duration = int(duration), #Needs to be cast to an int as it gets converted to an str when passsed in
        thumb = picon(channel),
        items = [
            MediaObject(
                container = container,
                video_codec = video_codec,
                audio_channels = 2,
                audio_codec = audio_codec,
                parts = [PartObject(key=Callback(PlayVideo, channel=channel))]
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


####################################################################################################
@route("video/dreambox/PlayVideo/{channel}")
def PlayVideo(channel, filename=None,  recorded=False):
    import urllib2, time
    from enigma2 import format_string, zap

    channel = channel.strip('.m3u8')
    if Prefs['zap'] and not recorded:
        #Zap to channel
        zap = zap(Prefs['host'], Prefs['port_web'], String.Quote(channel))
        if zap:
            Log('Zapped to channel when playing video')
        else:
            Log("Couldn't zap to channel when playing video")
    if not recorded:
        stream = 'http://{}:{}/{}'.format(Prefs['host'], Prefs['port_video'], channel)
        Log('Stream to play {}'.format(stream))
    else:

        filename = format_string(filename, clean_file=True)
        stream = 'http://{}:{}/file?file=/{}'.format(Prefs['host'], Prefs['port_web'], filename)
        Log('Recorded file  to play {}'.format(stream))

    return Redirect(stream)



@route("/video/dreambox/TimerPopup")
def TimerPopup(title, message):
    return     MessageContainer(
          title,
          message
      )


@route("/video/dreambox/TimerEvent")
def TimerEvent(title, message):

    oc = ObjectContainer()
    oc.add(InputDirectoryObject(key='www.google.co.uk',
                                   title='Timer',
                                   prompt='Click here to search for stuff',
                                   summary='Click here to search for stuff'
                                    )
    )
    return MessageContainer(
          'title',
          str(oc)
      )


##################################################
# Helpers                                        #
##################################################

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
def add_current_event(sRef=None, name=None, title=None, description=None, remaining=None, piconfile=None):
    # now check if we need to use the service
    Log ('Entered Add Current Event {} {} {} {} {} {}'.format(sRef, name, title, description, remaining, piconfile))
    if Client.Platform in CLIENT:
        return VideoClipObject(url='http://{}/{}/{}/{}'.format(Prefs['host'], Prefs['port_web'], Prefs['port_video'], sRef),
                               title='{}  - {}'.format(name, title),
                               summary='description',
                               thumb=picon(sRef))
    else:
        tuner = 1
        if title == 'N/A':
            tuner = get_packets(sRef)
        if tuner:
            return Display_Event(sender=title, channel=sRef, description=description, duration=remaining, thumb=picon(sRef))
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
    from enigma2 import get_current_service
    sRef, channel, provider, title, description, remaining = get_current_service(Prefs['host'], Prefs['port_web'])[0]
    if Client.Platform in CLIENT:
        result = VideoClipObject(url='http://{}/{}/{}/{}'.format(Prefs['host'], Prefs['port_web'], Prefs['port_video'], sRef),
                                           title='On Now - {}   {}'.format(channel, description))
    else:
        result = Display_Event(sender='On Now - {}   {}'.format(channel, title), channel=sRef, description=description, duration=int(remaining*1000))
    return result


##################################################################
# Adds a menu iem for the active timers                          #
##################################################################
def timers(oc):
    from enigma2 import get_timers

    timer = get_timers(Prefs['host'], Prefs['port_web'], active=True)

    if timer[0]:
        oc.add(DirectoryObject(key=Callback(TimerPopup,
                                 title='Timer',
                                 message='Active timer view Not working yet '),
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
# Calculates the remaingin time of the current event                   #
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
    if Prefs['picon'] :
        Log('Piconfile SRef for channels ****** {}'.format(sRef))
        piconfile = sRef.replace(':', '_')
        piconfile = piconfile.rstrip('_')
        piconfile = piconfile + '.png'
        piconpath = 'http://{}:{}/{}/'.format(Prefs['host'], Prefs['port_web'], Prefs['piconpath'].lstrip('/').rstrip('/'))
        Log(piconpath)
        return '{}{}'.format(piconpath, piconfile)
    else:
        return None


########################################################################
# Adds a menu item if the receiver just has one tuner                  #
########################################################################
def zap_menuitem(items=None):
    from enigma2 import get_number_of_tuners

    if get_number_of_tuners(Prefs['host'], Prefs['port_web']) == 1:
        items.append(DirectoryObject(key=Callback(ResetReceiver),
                               title='Reset receiver to original channel',
                               thumb = None))
    return items

@route("video/dreambox/ResetReceiver")
def ResetReceiver():
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
