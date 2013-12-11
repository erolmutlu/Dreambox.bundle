

ART = 'art-default.jpg'
ICON = 'icon-default.png'
LIVE_TV = 'live_tv.png'
RECORDED = 'recorded.png'
ZAP_TO_URL = 'http://%s:%s/web/zap?sRef=%s'
STREAM_URL = 'http://%s:%s/%s'
EPG_URL = 'http://%s:%s/web/epgnow?bRef=%s'






####################################################################################################
def Start():

    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items', cols=1)
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = 'Dreambox'
    DirectoryObject.thumb = R(ICON)



####################################################################################################
@handler('/video/dreambox', 'Dreambox', art=ART, thumb=ICON)
def MainMenu():
    #TODO Need to get breadscrumbs sorted out

    oc = ObjectContainer(view_group='InfoList', no_cache=True)

    oc.add(DirectoryObject(key=Callback(Bouquets),
                               title='Live TV',
                               tagline='Watch live TV direct from your Enigma 2 based satellite receiver',
                               thumb=R(LIVE_TV),
                               art=R(LIVE_TV),
                               duration=100)
    )
    oc.add(DirectoryObject(key='http://www.google.co.uk',
                               title='Recorded TV',
                               tagline='Watch recorded content on your Enigma 2 based satellite receiver',
                               thumb=R(RECORDED),
                               art=R(RECORDED),
                               duration=100)
    )
    oc.add(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))
    return oc


@route("/video/dreambox/Bouquets")
def Bouquets():
    from enigma2 import get_bouquets
    Log('Entering Bouquets to fetch bouquets from sat box')

    oc = ObjectContainer(view_group='InfoList', title1='Bouquets')
    bouquets = None
    if Prefs['host'] and Prefs['port_web']:
        bouquets = get_bouquets(Prefs['host'], Prefs['port_web'])
    if bouquets and bouquets[0][0] != 'Error':
        for name, ref in bouquets:
            oc.add(DirectoryObject(key=Callback(Channels, bref=ref),
                               title=name)
            )
    else:
        Log.Error(bouquets)
    return oc

# need to get the channels and store them as movie objects.
#can store the picons in them
# THe urls will point to the UrlService, which will get the epg data for the episodes in the channel
@route("/video/dreambox/Channels/{bref}")
def Channels(bref):
    from enigma2 import get_channels
    Log('Entering Channels to fetch channels from sat box')

    oc = ObjectContainer(view_group='InfoList', title1='Channels')
    channels = None
    if Prefs['host'] and Prefs['port_web']:
        channels = get_channels(Prefs['host'], Prefs['port_web'], bref)
    if channels and channels[0] != 'Error':
        Log(channels[0])
        for id, start, duration, current_time, title, description, sRef, name in channels:
            remaining = ((current_time + duration) - current_time) * 1000
            oc.add(DirectoryObject(key=Callback(ChannelContent, sRef=sRef),
                                   title='{}  - {}'.format(name, title),
                                   duration=remaining
                                   )
                  )
    else:
        Log.Error(channels)
    return oc



@route("/video/dreambox/ChannelContent/{sRef}")
def ChannelContent(sRef):
    from enigma2 import get_nownext
    import time
    Log('Entering ChannelContent to fetch channel contents from sat box')

    oc = ObjectContainer(view_group='InfoList', title1='Channel Content')
    channel_content = None
    if Prefs['host'] and Prefs['port_web']:
        #This is rhe same as ITV player parsing the episodes
        channel_content = get_nownext(Prefs['host'], Prefs['port_web'], sRef)
        Log(channel_content)
    if channel_content and channel_content[0] != 'Error':
        for id, start, duration, current_time, title, description, sRef, name in channel_content:
            remaining = ((current_time + duration) - current_time) * 1000
            # TODO We need to create video clip objects here that pass the url of our service in
            # TODO I ONLY NEED TO SET THE VURRENT VIDEO TO THR URL AS THE OTHERD DONT EXIST. REREOUTE THEM TO ANOTHER CALLBACK AND HANDLE THE TIMER
            # TODO Could we use the epg search to search for name etc to retreive it again when we press play
            # TODO here we will see the full description etc. .....Or event type now or future ??
            # TODO We need to figure out JUST PASS AN EXTRA PARAM INTO THE THING HTTP192.....?NOW=TRUE, NEXT=FALSE ETC.
            # todo wE CAN THEN FIGURE OUT WHAT CALL TO DO IN THE URL TO GET DATA AGAIN
            if int(start) < time.time():
                oc.add(VideoClipObject(url='http://192.168.1.252/web/epgservicenow?sRef=1:0:1:1933:7FF:2:11A0000:0:0:0:',
                                   title='{}  - {}'.format(name, title),
                                   summary=description
                                   )
                  )
            else:
                # Go off and set a timer
                #TODO This can have invalid xml in so needs to be converted. That swhy you get blank lines
                oc.add(DirectoryObject(key=Callback(TimerPopup, name=name), title=title,
                summary="Click here to search for stuff")

    )
    else:
        Log.Error(channel_content)
    return oc


@route("/video/dreambox/TimerPopup")
def TimerPopup(name):
    return MessageContainer(
          "Timer",
          "Timer created for {}".format(name)
      )












@route("/video/dreambox/BouquetsMenu/{name}")
def BouquetsMenu(sender, index, name):
	
	#Getting Channels and EPG
	url = EPG_URL % (Prefs['host'], Prefs['port_web'], String.Quote(index))
	Log(url)
	try:
		urlHtml = HTML.ElementFromURL(url)
	except:
		Log("Couldn't get channels and EPG.") 
	events = urlHtml.xpath("//e2event")
	ChannelReference = list()
	ChannelName = list()
	epgdescription = list()
	epgduration = list()
	# Should be able to get now and next here
	# I'll refactor this out
	for event in events:
		tempChannelReference = ''
		tempChannelName = ''
		if len(event.xpath("./e2eventservicereference/text()"))>0:
			tempChannelReference = event.xpath("./e2eventservicereference/text()")[0]
		if len(event.xpath("./e2eventservicename/text()"))>0:
			tempChannelName = event.xpath("./e2eventservicename/text()")[0]
		if Prefs['epg']:
			temptitle = ''
			tempdescription = ''
			tempdescriptionext = ''
			tempcurrenttime = ''
			tempstart = ''
			tempduration = ''
			if len(event.xpath("./e2eventtitle/text()"))>0:
				temptitle = event.xpath("./e2eventtitle/text()")[0]
			if len(event.xpath("./e2eventdescription/text()"))>0:
				tempdescription = event.xpath("./e2eventdescription/text()")[0]
			if len(event.xpath("./e2eventdescriptionextended/text()"))>0:
				tempdescriptionext = event.xpath("./e2eventdescriptionextended/text()")[0]
			if len(event.xpath("./e2eventcurrenttime/text()"))>0:
				tempcurrenttime = event.xpath("./e2eventcurrenttime/text()")[0]
			if len(event.xpath("./e2eventstart/text()"))>0:
				tempstart = event.xpath("./e2eventstart/text()")[0]
			if len(event.xpath("./e2eventduration/text()"))>0:
				tempduration = event.xpath("./e2eventduration/text()")[0]
			if temptitle == 'None':
				temptitle = ''
			if tempstart == 'None':
				tempstart = ''
			if tempdescription == 'None':
				tempdescription = ''
			if tempdescriptionext == 'None':
				tempdescriptionext = ''
			if tempduration == 'None':
				tempduration = ''
			if not temptitle == '':
				tempChannelName = tempChannelName+' ('+temptitle+')'
			if not tempstart == '':
				tempChannelName = tempChannelName+' +'+str((int(tempcurrenttime)-int(tempstart))//60)
			if not tempdescriptionext == '':
				tempdescription = tempdescription + '\n\n' + tempdescriptionext
			epgdescription.append(tempdescription)
			if not tempduration == '':
				epgduration.append(tempduration)
			else:
				epgduration.append('0')	
		else:
			epgdescription.append('')
			epgduration.append('0')
		ChannelReference.append(tempChannelReference)
		ChannelName.append(tempChannelName)
	Log('ChannelReference='+str(len(ChannelReference)))
	Log('ChannelName='+str(len(ChannelName)))
	Log('epgdescription='+str(len(epgdescription)))
	Log('epgduration='+str(len(epgduration)))
		
	oc = ObjectContainer(title2=name, view_group='List', no_cache=True)

	for item in xrange(len(ChannelReference)):
		oc.add(TvStationMenu(sender=ChannelName[item], channel=ChannelReference[item], epgdescription=epgdescription[item], epgduration=epgduration[item]))

	return oc

##11111##################################################################################################
@route("/video/dreambox/TvStationMenu")
def TvStationMenu(sender, channel, epgdescription, epgduration, thumb=R(ICON), include_oc=False):
    browsers = ('Chrome', 'Internet Explorer', 'Opera', 'Safari', 'iOS', 'Plex Home Theater')
    video_codec = 'h264'
    audio_codec = 'mp3'
    container = 'mp4'
    if Prefs['picon']:
		piconfile = channel.replace(':', '_')
		piconfile = piconfile.rstrip('_')
		piconfile = piconfile + '.png'
		if piconfile:
			Log('Piconfile: '+sender+ ' - ' + piconfile)
			thumb=R(piconfile)
    # Set default container for MP4 to work on Samsung.. and others???
	# Just filters against browser name (Better way to do this ? Check the caps of the connected device?)
    Log('******' + str(Client.Platform))
    if (Client.Platform  in browsers ):
        container = 'mpegts'
    video = VideoClipObject(
		key = Callback(TvStationMenu, sender=sender, channel=channel, epgdescription=epgdescription, epgduration=epgduration, thumb=thumb, include_oc=True),
		rating_key = channel,
		title = sender,
		summary = epgdescription,
		duration = int(epgduration)*1000,
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
	Log('channel variable='+channel)
	if Prefs['zap']:
		#Zap to channel
		url = ZAP_TO_URL % (Prefs['host'], Prefs['port_web'], String.Quote(channel))
		try:
			urlHtml = HTTP.Request(url, cacheTime=0, sleep=2.0).content
			Log('url HTML = {}'.format(urlHtml))
		except:
			Log("Couldn't zap to channel.")
	stream = STREAM_URL % (Prefs['host'], Prefs['port_video'], channel)
	Log('stream is {}'.format(stream))
	return Redirect(stream)
