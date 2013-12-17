ART = 'art-default.jpg'
ICON = 'icon-default.png'
ZAP_TO_URL = 'http://%s:%s/web/zap?sRef=%s'
STREAM_URL = 'http://%s:%s/%s'
EPG_URL = 'http://%s:%s/web/epgnow?bRef=%s'
CLIENT = ['Plex Home Theater']

####################################################################################################
def Start():

    Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = 'Dreambox'
    DirectoryObject.thumb = R(ICON)

####################################################################################################

@handler('/video/dreambox', 'Dreambox', art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer(view_group='List', no_cache=True)
    oc.add(DirectoryObject(key=Callback(Display_Bouquets),
                               title='Live TV',
                               tagline='Watch live TV direct from your Enigma 2 based satellite receiver')
    )
    oc.add(DirectoryObject(key=Callback(Display_Movies),
                               title='Recorded TV',
                               tagline='Watch recorded content on your Enigma 2 based satellite receiver')
    )
    oc.add(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    return oc


@route("/video/dreambox/Display_Bouquets")
def Display_Bouquets():
    from enigma2 import get_bouquets

    oc = ObjectContainer(view_group='List', no_cache=True, title1='Live TV')
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:

        bouquets = get_bouquets(Prefs['host'],Prefs['port_web'])
        Log(bouquets)
        for bouquet, index in bouquets:
            oc.add(DirectoryObject(key = Callback(Display_Bouquet_Channels, sender = str(bouquet), index=str(index)),
                                    title = str(bouquet)))
        oc.add(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))      
        return oc


@route("/video/dreambox/Display_Movies")
def Display_Movies():
    from enigma2 import get_movies

    oc = ObjectContainer(view_group='List', no_cache=True, title1='Recorded TV')
    if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:

        movies = get_movies(Prefs['host'],Prefs['port_web'])
        Log(movies)
        for sref, title, description, channel, e2time, length, filename in movies:
            oc.add(DirectoryObject(key = Callback(Display_Bouquet_Channels, sender = str(channel), index=str(filename)),
                                    title ='{} ({})'.format(title, e2time),
                                    summary=description))
        return oc

@route("/video/dreambox/Display_Bouquet_Channels/{name}")
def Display_Bouquet_Channels(sender, index):

    from enigma2 import get_channels

    channels = get_channels(Prefs['host'], Prefs['port_web'], index)
    name = sender

    oc = ObjectContainer(title2=name, view_group='List', no_cache=True)
    for id, start, duration, current_time, title, description, sRef, name in channels:
        remaining = ((current_time + int(duration)) - current_time) * 1000
        oc.add(DirectoryObject(key = Callback(Display_Channel_Events, sender=str(name), index=str(sRef)),
                                    title = '{}  - {}'.format(name, title),
                                    duration = remaining))

    return oc

@route("/video/dreambox/Display_Channel_Events/{sender}")
def Display_Channel_Events(sender, index):
    from enigma2 import get_nownext, get_fullepg
    import time
    if Prefs['fullepg']:
        events = get_fullepg(Prefs['host'], Prefs['port_web'], index)
    else:
        events = get_nownext(Prefs['host'], Prefs['port_web'], index)
    oc = ObjectContainer(title2=sender, view_group='List', no_cache=True)
    for id, start, duration, current_time, title, description, sRef, name in events:
        remaining = ((current_time + int(duration)) - current_time) * 1000
        #duration *= 1000
        if int(start) < time.time():
            # now check if we need to use theservice
            if Client.Platform in CLIENT:
                oc.add(VideoClipObject(url='http://{}:{}/{}'.format(Prefs['host'], Prefs['port_video'],index),
                                       title='{}  - {}'.format('name', 'title'),
                                       summary='description'
                                       )
                       )
            else:
                oc.add(Display_Event(sender=title, channel=sRef, description=description, duration=int(duration)))
        else:
            oc.add(DirectoryObject(key=Callback(TimerPopup,
                                   title='Timer',
                                   message='Timer created for \n\n{} {} *** Not working yet ***'.format(name, title)),
                                   title=title,
                                   duration = duration * 1000,
                                   summary='Click here to search for stuff'),

            )
    return oc


##11111##################################################################################################
@route("/video/dreambox/Display_Event")
def Display_Event(sender, channel, description, duration, thumb=R(ICON), include_oc=False):
    # x264 soesnt work with samsung, probably iOs.
    Log('**** TVStation  sender {}, channel {}, description {}, duration {}'.format(sender, channel, description, duration))
    browsers = ('Chrome', 'Internet Explorer', 'Opera', 'Safari')
    video_codec = 'h264'
    audio_codec = 'mp3'
    container = 'mp4'
    if Prefs['picon']:
        piconfile = channel.replace(':', '_')
        piconfile = piconfile.rstrip('_')
        piconfile = piconfile + '.png'
        if piconfile:
            Log('Piconfile: '+sender+ ' - ' + piconfile)
    if (Client.Platform  in browsers ):
        container = 'mpegts'
    video = VideoClipObject(
        key = Callback(Display_Event, sender=sender, channel=channel, description=description, duration=duration, thumb=thumb, include_oc=True),
        rating_key = channel + description,
        title = sender,
        summary = description,
        duration = int(duration)*1000,
        thumb = thumb,
        items = [
            MediaObject(
                container = container,
                video_codec = video_codec,
                audio_codec = audio_codec,
                audio_channels = 2,
                parts = [PartObject(key=Callback(PlayVideo, channel=channel))]
            )
        ]
    )
    if include_oc:
        oc = ObjectContainer()
        oc.add(video)
        return oc
    return video


####################################################################################################
@route("video/dreambox/PlayVideo/{channel}")
def PlayVideo(channel):

    channel = channel.strip('.m3u8')
    if Prefs['zap']:
        #Zap to channel
        zap()
        url = ZAP_TO_URL % (Prefs['host'], Prefs['port_web'], String.Quote(channel))
        try:
            urlHtml = HTTP.Request(url, cacheTime=0, sleep=2.0).content
            Log('url HTML = {}'.format(urlHtml))
        except:
            Log("Couldn't zap to channel.")

    stream = 'http://{}:{}/{}'.format(Prefs['host'], Prefs['port_video'], channel)
    return Redirect(stream)

@route("/video/dreambox/TimerPopup")
def TimerPopup(title, message):
    return MessageContainer(
          title,
          message
      )