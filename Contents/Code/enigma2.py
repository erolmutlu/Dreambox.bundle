
import urllib
from BeautifulSoup import BeautifulSoup



def get_bouquets(host, web):

    url = 'http://{}:{}/web/getservices'.format(host, web)
    soup = get_data((url, None))
    results = get_service_name(soup)
    return results


def get_current_service(host, web):

    url = 'http://{}:{}/web/getcurrent'.format(host, web)
    try:
        soup = get_data((url, None))
        results = get_current_service_info(soup)
    except:
        raise
    return results

def get_channels_from_service(host, web, sRef, show_epg=False):

    url = 'http://{}:{}/web/getservices'.format(host, web)
    data = {'sRef': sRef}
    soup = get_data((url, data))
    results = get_service_name(soup, host, web, show_epg)
    return results


def get_channels_from_epg(host, web, bRef):

    url = 'http://{}:{}/web/epgbouquet'.format(host, web)
    data = {'bRef': bRef}
    soup = get_data((url, data))
    results = get_events(soup)
    return results


def get_fullepg(host, web, sRef):

    url = 'http://{}:{}/web/epgservice'.format(host, web)
    data = {'sRef': sRef}
    soup = get_data((url, data))
    results = get_events(soup)
    return results

def get_now(host, web, sRef):

    url = 'http://{}:{}/web/epgservicenow'.format(host, web)
    data = {'sRef': sRef}
    soup = get_data((url, data))
    results = get_events(soup)
    return results


def get_nownext(host, web, sRef):

    url = 'http://{}:{}/web/epgservicenow'.format(host, web)
    url2 = 'http://{}:{}/web/epgservicenext'.format(host, web)
    data = {'sRef': sRef}
    soup = get_data((url, data), (url2, data))
    results = get_events(soup)
    return results


def get_movies(host, web):

    movies = []
    url = 'http://{}:{}/web/movielist'.format(host, web)
    try:
        soup = get_data((url, None))
        for elem in soup[0].findAll('e2movie'):
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
            movies.append((format_string(sref),
                           format_string(title, strip=True),
                           format_string(description, strip=True),
                           format_string(channel, strip=True),
                           dt,
                           format_string(length),
                           format_string(filename, strip=True)))

    except Exception as e:
        return 'Error', 'getmovies Messsage and vals : {} host: {} port: {}  url: {}'.format(e.message, host, web, url)
    return movies

#TODO Returning the wrong result when eventid was incorrectly named. eventID
def set_timer(host, web, sRef, eventID):
    #http://192.168.1.252/web/timeraddbyeventid?sRef=1:0:1:2077:7FA:2:11A0000:0:0:0:&eventid=674
    state = False
    error = ''
    try:
        url = 'http://{}:{}/web/timeraddbyeventid'.format(host, web)
        data = {'sRef': sRef, 'eventid': eventID}
        soup = get_data((url, data))
        state = soup[0].e2state.string
        if state == 'True':
            state = True
    except Exception as e:
        error = e.message
    return state, error


def delete_timer(host, web, sRef=None, begin=0, end=0):
    #http://192.168.1.252/web/timerdelete?sRef=1:0:19:2710:801:2:11A0000:0:0:0:&begin=1388863020&end=1388868780
    state = False
    error = ''
    try:
        url = 'http://{}:{}/web/timerdelete'.format(host, web)
        data = {'sRef': sRef, 'begin': begin, 'end': end}
        soup = get_data((url, data))
        state = soup[0].e2state.string
        if state == 'True':
            state = True
    except Exception as e:
        error = e.message
    return state, error

def get_timers(host, web, active=False):
    #not using active yet
    import time
    timers = []
    url = 'http://{}:{}/web/timerlist'.format(host, web)
    try:
        soup = get_data((url, None))
        soup = soup[0].findAll('e2timer')
        for elem in soup:
            sref, service_name, name, description, disabled, begin, end, duration = elem.findAll(['e2servicereference',
                                                                            'e2servicename',
                                                                            'e2name',
                                                                            'e2description',
                                                                            'e2disabled',
                                                                            'e2timebegin',
                                                                            'e2timeend',
                                                                            'e2duration'
                                                                       ])
            if long(format_string(begin)) > time.time():
                timers.append((format_string(sref),
                           format_string(service_name, strip=True),
                           format_string(name, strip=True),
                           format_string(description, strip=True),
                           bool(format_string(disabled)),
                           int(format_string(begin)),
                           int(format_string(end)),
                           int(format_string(duration)))
            )
    except Exception as e:
        return 'Error', 'Messsage and vals : {} host: {} port: {}  url: {}'.format(e.message, host, web, url)
    return timers



def get_number_of_tuners(host, web):
    url = 'http://{}:{}/web/about'.format(host, web)
    try:
        soup = get_data((url, None))
        number_of_tuners = len(soup[0].findAll('e2nim'))
    except:
        raise
    return number_of_tuners

def get_number_of_audio_tracks(host, web):
    url = 'http://{}:{}/web/getaudiotracks'.format(host, web)
    try:
        soup = get_data((url, None))
        number_of_audio_tracks = len(soup[0].findAll('e2audiotrack'))
    except:
        raise
    return number_of_audio_tracks

def get_audio_tracks(host, web):
    url = 'http://{}:{}/web/getaudiotracks'.format(host, web)
    audio_tracks = []
    try:
        soup = get_data((url, None))
        soup = soup[0].findAll('e2audiotrack')
        for elem in soup:
            description, trackid, active = elem.findAll(['e2audiotrackdescription',
                                                         'e2audiotrackid',
                                                         'e2audiotrackactive'])
            audio_tracks.append((int(trackid.string), description.string, bool(active.string)))

    except:
        raise
    return audio_tracks

def set_audio_track(host, web, trackid):

    result = False
    error = ''
    try:
        url = 'http://{}:{}/web/selectaudiotrack'.format(host, web)
        data = {'id': trackid}
        soup = get_data((url, data))
        state = soup[0].e2result.string
        if state == 'Success':
            result = True
    except:
        raise
    return result, error



def zap(host, web, sRef):

    result = False
    error = ''
    try:
        url = 'http://{}:{}/web/zap'.format(host, web)
        data = {'sRef': sRef}
        soup = get_data((url, data))
        state = soup[0].e2state.string
        if state == 'True':
            result = True
    except:
        raise
    return result, error

#################################
# Helpers                       #
#################################

###############################################################
# Extracts the service name from the soup                     #
###############################################################
def get_service_name(soup_list, host=None, web=None, show_epg=False):
    try:
        results = []
        for soup in soup_list:
            for elems in soup.findAll('e2service'):
                sRef, name = elems.findAll(['e2servicereference', 'e2servicename'])
                if show_epg:
                    re =  get_now(host, web, format_string(sRef))
                    if re[0] != 'Error':
                        results.append((re[0][0],
                                     re[0][1],
                                     re[0][2],
                                     re[0][3],
                                     format_string(re[0][4], strip=True),
                                     format_string(re[0][5], strip=True),
                                     format_string(re[0][6]),
                                     format_string(re[0][7], strip=True)))
                    else:
                        results.append((0, 0,  0,  0,
                                     '',
                                     '',
                                     format_string(sRef),
                                     format_string(name, strip=True)))
                else:
                    results.append((0,  0,  0,  0,
                                     '',
                                     '',
                                     format_string(sRef),
                                     format_string(name, strip=True)))
    except Exception as e:
        return 'Error', 'getservicename Messsage  : {} '.format(e.message)
    return results


###############################################################
# Extracts the events from the soup                           #
###############################################################
def get_events(soup_list):

    results = []
    try:
        for soup in soup_list:
            for elems in soup.findAll('e2event'):
                id, start, duration, current_time, title, description, sRef, name = elems.findAll(['e2eventid',
                                                                                    'e2eventstart',
                                                                                    'e2eventduration',
                                                                                    'e2eventcurrenttime',
                                                                                    'e2eventtitle',
                                                                                    'e2eventdescription',
                                                                                    'e2eventservicereference',
                                                                                    'e2eventservicename'])

                results.append((format_string(id, integer=True),
                                     format_string(start, integer=True),
                                     format_string(duration, integer=True),
                                     format_string(current_time, integer=True),
                                     format_string(title, strip=True),
                                     format_string(description, strip=True),
                                     format_string(sRef),
                                     format_string(name, strip=True)))

    except Exception as e:
        return 'Error', 'Messsage  : {} '.format(e.message)
    return results

###############################################################
# Extracts the current service info from the soup             #
###############################################################
def get_current_service_info(soup_list):

    results = []
    try:
        for soup in soup_list:
            for elems in soup.findAll('e2event'):
                sRef, channel, provider,title, description, remaining = elems.findAll(['e2eventservicereference',
                                                      'e2eventservicename',
                                                      'e2eventprovidername',
                                                      'e2eventtitle',
                                                      'e2eventdescription',
                                                      'e2eventremaining'])

                results.append((format_string(sRef),
                                format_string(channel, strip=True),
                                format_string(provider, strip=True),
                                format_string(title, strip=True),
                                format_string(description, strip=True),
                                format_string(remaining, integer=True)))

    except Exception as e:
        return 'Error', 'Messsage  : {} '.format(e.message)
    return results


###############################################################
# Formats the string returned from the satellite box          #
###############################################################
def format_string(data, strip=False, clean_file=False, integer=False):
    if data:
        if isinstance(data, unicode):
            data = data.encode('ascii', 'ignore')
        else:
            try:
                data = data.string
            except:
                data = str(data)
        if data not in (None, 'None'):
            if len(data) > 0:
                if strip:
                    data = unicode_replace(data)
                if clean_file:
                    data = clean_filename(data)
                if integer:
                    return int(data)
                return data
    if integer:
        return 0
    return ''


###############################################################
# Remove Unicode Chars sent via the mpeg stream               #
###############################################################
def unicode_replace(data):
    invalid_chars = {u'\x86': '',
                     u'\x87': '',
                     '&amp;': '&',
                    '&gt;': '>'}
    for k, v in invalid_chars.iteritems():
        data = data.replace(k, v)
    return data


###############################################################
# Remove HTML escape chars that are not replaced              #
###############################################################
def clean_filename(data):
    escape_chars = {'++': ' %2B',
                    '+': '%20',
                    '&': '%26',
                    ' ': '%20',
                    '<': '%3C',
                    '>': '%3E',
                    '#': '%23',
                    '%': '%25',
                    '\\': '%5C',
                    '^': '%5E'}
    for k, v in escape_chars.iteritems():
        data = data.replace(k, v)
    return data


###############################################################
# Gets the stuff we need from the box and returns soup        #
###############################################################
def get_data(*args):
    from httplib2 import Http
    from urllib import urlencode
    req = Http(timeout=2)
    results = []
    for item in args:
        u = item[0]
        data = item[1]
        print data
        try:
            if data:
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                resp, content = req.request(u, "POST", headers=headers, body=urlencode(data))
                print resp

                print content
            else:
                resp, content = req.request(u, "GET", data)
            soup = BeautifulSoup(content)
            results.append(soup)
        except:
            raise
    return results


