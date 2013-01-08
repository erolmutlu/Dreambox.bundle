ART = 'art-default.jpg'
ICON = 'icon-default.png'
REGEX = '%s = new Array\((.+?)\);'
ZAP_TO_URL = 'http://%s:%s/cgi-bin/zapTo?path=%s&curBouquet=%d&curChannel=%d'

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

	if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:
		categories = GetDataList(name='bouquets')

		if not categories:
			return ObjectContainer(header="Error", message="Couldn't connect to host")

		for bouquet_index, title in enumerate(categories):
			channels = GetDataList(name='channels\[%d\]' % bouquet_index)

			if channels[0].lower() == 'none':
				continue

			oc.add(DirectoryObject(
				key = Callback(Bouquet, title=title, bouquet_index=bouquet_index),
				title = title
			))

	oc.add(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))

	return oc

####################################################################################################
@route('/video/dreambox/bouquet/{bouquet_index}', bouquet_index=int)
def Bouquet(title, bouquet_index):

	oc = ObjectContainer(title2=title, view_group='List', no_cache=True)
	channels = GetDataList(name='channels\[%d\]' % bouquet_index)
	channel_refs = GetDataList(name='channelRefs\[%d\]' % bouquet_index)

	for channel_index, title in enumerate(channels):
		video = CreateVideoClipObject(channel_ref=channel_refs[channel_index], bouquet_index=bouquet_index, channel_index=channel_index, title=title)
		oc.add(video)

	return oc

####################################################################################################
def GetDataList(name):

	url = 'http://%s:%s/body' % (Prefs['host'], Prefs['port_web'])

	try:
		body = HTTP.Request(url, cacheTime=30).content
	except:
		return None

	list = Regex(REGEX % name, Regex.DOTALL).search(body)
	if list:
		list = list.group(1).strip()
		list = list.strip('"').split('", "')

		return list

	return None

####################################################################################################
def CreateVideoClipObject(channel_ref, bouquet_index, channel_index, title, thumb=R(ICON), include_oc=False):

	video = VideoClipObject(
		key = Callback(CreateVideoClipObject, channel_ref=channel_ref, bouquet_index=bouquet_index, channel_index=channel_index, title=title, thumb=thumb, include_oc=True),
		rating_key = channel_ref,
		title = title,
		thumb = thumb,
		items = [
			MediaObject(
				container = 'mpegts',
				video_codec = 'mpeg2',
				audio_codec = AudioCodec.MP3,
				audio_channels = 2,
				parts = [
					PartObject(
						key = Callback(PlayVideo, channel_ref=channel_ref, bouquet_index=bouquet_index, channel_index=channel_index)
					)
				]
			)
		]
	)

	if include_oc:
		oc = ObjectContainer()
		oc.add(video)
		return oc
	else:
		return video

####################################################################################################
def PlayVideo(channel_ref, bouquet_index, channel_index):

	zap_to = ZAP_TO_URL % (Prefs['host'], Prefs['port_web'], channel_ref, bouquet_index, channel_index)
	Log(' --> %s' % zap_to)

	return None
