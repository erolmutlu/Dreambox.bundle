##############################################
#  Module to get metadata for our tv data    #
##############################################

from httplib2 import Http
from pytvdbapi import api

import io
API_KEY = '6DBA02A9110F1444'

###############################################
#
def get_thumb(id=None, series=None, language='en', scale=False):
    thumb = None
    if not id:
        tv = api.TVDB(API_KEY, banners=True)
        result = tv.search(series, language, cache=True)

        if result:
            series = result[0]
            #can store the id's
            domain =  tv.mirrors.data.pop(0).url
            #only get one banner
            #if we do anupdate we get full attribute list
            url =  domain +'/banners/fanart/original/' + str(series.id) + u'-1.jpg'
            if scale:
                thumb = get_image(imageURL=url, scale=True)
            else:
                thumb = get_image(imageURL=url)
            #file = io.open('AppData\\Local\\Plex Media Server\\Plug-ins\\Dreambox.bundle\\Contents\\Resources\\{}.jpg'.format(series.id), 'wb')
            #file.write(thumb)
            #file.close()
        return thumb

def get_series_id(series=None, language='en'):
    tv = api.TVDB(API_KEY)
    result = tv.search(series, language, cache=True)

    if result:
        series = result[0]
        return series.id
    return None






def get_image(imageURL='', width=300, height=300, scale=False):
    if scale:
        url = 'http://127.0.0.1:32400/photo/:/transcode?url={}&width={}&height={}'.format(imageURL, width, height)
    else:
        url = imageURL
    req = Http(timeout=5)

    try:
        headers = {'Content-type': 'image/jpeg'}
        resp, content = req.request(url, "GET", headers=headers)
    except:
        raise
    return content



