
import urllib2
from BeautifulSoup import BeautifulSoup


def get_bouquets(host, web):
    bouquets = []
    url = 'http://{}:{}/web/getservices'.format(host, web)
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        for elems in soup.findAll('e2service'):
            bref, name = elems.findAll(['e2servicereference', 'e2servicename'])
            bouquets.append((name.string, bref.string))
    except Exception as e:
        return 'Error', 'Messsage and vals : {} host: {} port: {}'.format(e.message, host, web)
    return bouquets



def get_channels(host, web, bRef):
    import urllib
    channels = []
    url = 'http://{}:{}/web/epgbouquet'.format(host, web)
    data = urllib.urlencode({'bRef': bRef})
    try:
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        soup = BeautifulSoup(response.read())
        for elems in soup.findAll('e2event'):
            id, start, duration, current_time, title, description, sRef, name = elems.findAll(['e2eventid',
                                                                            'e2eventstart',
                                                                            'e2eventduration',
                                                                            'e2eventcurrenttime',
                                                                            'e2eventtitle',
                                                                            'e2eventdescription',
                                                                            'e2eventservicereference',
                                                                            'e2eventservicename'])

            channels.append((int(format_string(id)),
                             int(format_string(start)),
                             int(format_string(duration)),
                             int(format_string(current_time)),
                             format_string(title, strip=True),
                             format_string(description, strip=True),
                             format_string(sRef),
                             format_string(name)))

    except Exception as e:
        return 'Error', 'Messsage and vals : {} host: {} port: {} bref: {} url: {}'.format(e.message, host, web, bRef, url)
    return channels

def get_fullepg(host, web, sRef):
    import urllib
    channels = []
    url = 'http://{}:{}/web/epgservice'.format(host, web)
    data = urllib.urlencode({'sRef': sRef})
    try:
        soup = get_data((url, data))
        soup = soup[0].findAll('e2event')
        for elem in soup:
            id, start, duration, current_time, title, description, sRef, name = elem.findAll(['e2eventid',
                                                                            'e2eventstart',
                                                                            'e2eventduration',
                                                                            'e2eventcurrenttime',
                                                                            'e2eventtitle',
                                                                            'e2eventdescription',
                                                                            'e2eventservicereference',
                                                                            'e2eventservicename'])

            channels.append((int(format_string(id)),
                             int(format_string(start)),
                             int(format_string(duration)),
                             int(format_string(current_time)),
                             format_string(title, strip=True),
                             format_string(description, strip=True),
                             format_string(sRef),
                             format_string(name)))

    except Exception as e:
        return 'Error', 'Messsage and vals : {} host: {} port: {} bref: {} url: {}'.format(e.message, host, web, sRef, url)
    return channels

def get_nownext(host, web, sRef):
    import urllib
    channels = []
    url = 'http://{}:{}/web/epgservicenow'.format(host, web)
    url2 = 'http://{}:{}/web/epgservicenext'.format(host, web)
    data = urllib.urlencode({'sRef': sRef})

    try:
        soup = get_data((url, data), (url2, data))
        for elem in soup:
            id, start, duration, current_time, title, description, sRef, name = elem.findAll(['e2eventid',
                                                                            'e2eventstart',
                                                                            'e2eventduration',
                                                                            'e2eventcurrenttime',
                                                                            'e2eventtitle',
                                                                            'e2eventdescription',
                                                                            'e2eventservicereference',
                                                                            'e2eventservicename'])

            channels.append((int(format_string(id)),
                             int(format_string(start)),
                             int(format_string(duration)),
                             int(format_string(current_time)),
                             format_string(title, strip=True),
                             format_string(description, strip=True),
                             format_string(sRef),
                             format_string(name)))

    except Exception as e:
        return 'Error', 'Messsage and vals : {} host: {} port: {} bref: {} url: {}'.format(e.message, host, web, sRef, url)
    return channels


def get_movies(host, web):
    import urllib
    movies = []
    url = 'http://{}:{}/web/movielist'.format(host, web)
    try:
        soup = get_data((url, None))
        soup = soup[0].findAll('e2movie')
        print soup
        for elem in soup:
            sref, title, description, channel, e2time, length, filename = elem.findAll(['e2servicereference',
                                                                            'e2title',
                                                                            'e2description',
                                                                            'e2eventcurrenttime',
                                                                            'e2servicename',
                                                                            'e2time',
                                                                            'e2length',
                                                                            'e2filename'
                                                                            ])
            import datetime
            dt = datetime.datetime.fromtimestamp(int(format_string(e2time))).strftime('%d %B %Y %H:%M')
            print dt
            movies.append((format_string(sref),
                           format_string(title, strip=True),
                           format_string(description, strip=True),
                           format_string(channel, strip=True),
                           dt,
                           format_string(length),
                           format_string(filename)))

    except Exception as e:
        return 'Error', 'Messsage and vals : {} host: {} port: {}  url: {}'.format(e.message, host, web, url)
    return movies





#################################
# Helpers                       #
#################################





def format_string(data, strip=False):
    if data.string:
        if len(data.string) > 0:
            if strip:
                return unicode_replace(data.string)
            return data.string
    return ''

###############################################################
# Remove Unicode Chars sent via the mpeg stream               #
###############################################################
def unicode_replace(data):
    invalid_chars = {u'\x86': '',
                     u'\x87': '',
                     '&amp;': '&'}
    for k, v in invalid_chars.iteritems():
        data = data.replace(k, v)
    return data

def get_data(*args):
    import urllib2
    results = []
    for item in args:
        u = item[0]
        #TODO Need to do a check here to make sure it exists
        data = item[1]
        try:
            if data:
                req = urllib2.Request(u, data)
            else:
                req = urllib2.Request(u)
            response = urllib2.urlopen(req)
            soup = BeautifulSoup(response.read())
            results.append(soup)
        except Exception as e:
            results.append(('Error', e.message))
    return results


#res =  get_channels('192.168.1.252', 80, '1:7:1:0:0:0:0:0:0:0:FROM%20BOUQUET%20"userbouquet.entertainment.tv"')


#for r in res:
#    print repr(r[4])

#print get_fullepg('192.168.1.252', 80, '1:0:1:1933:7FF:2:11A0000:0:0:0:')

print get_movies('192.168.1.252', 80)
