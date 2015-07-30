import logging
from httplib2 import Http
from urllib import urlencode
from BeautifulSoup import BeautifulSoup as Soup
import time
import sys
from database import DB


escape = lambda x : x.decode('utf8').encode('windows-1252', errors='ignore') if x else None

EARLIEST_STAR_TIME = """Select MAX(event_start) AS event_start from Channel
  inner JOIN Event
  ON Event.ch_id = Channel.service_reference
  GROUP BY Channel.service_reference
  order by event_start ASC
  LIMIT 1"""

LAST_SCANNED = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.LastScanned.tv" ORDER BY bouquet'

dev = 0


def message(x):
    try:
        if dev:
            logging.info(x)
        else:
            Log(str(x))
    except NameError:
        pass

class Receiver():

    def __init__(self):

        self.db = DB()

        self.host = ''
        self.port = 0
        self.username = ''
        self.password = ''
        self.no_of_tuners = ''
        self.zap = False
        self.timers = {}
        self.connected = False
        self.current_event = ''

    def is_connected(self):

        return self.connected

    def setup(self, **kwargs):

        message('Setting up object')

        self.host = kwargs.get('host', '')
        self.port = kwargs.get('port', 0)


        self.process_device_info()
        self.bouquets()
        message('Finished setting up')

    def update_database(self):

        #todo purge old events, older than now minus 12 hours ago.
        #todo get bouquets, channels etc. get rid of any old channels that no longer link to bouquets etc

        pass

    def process_device_info(self):
        """
        Issues a /web/deviceinfoo command to the receiver and processes the result.

        """

        def parse_device_info( deviceinfo):
            """
            Takes the deviceinfo that was returned by the receiver, parses the XML and
             populates the requires properties
            """
            self.no_of_tuners = len(Soup(deviceinfo).findAll('e2frontend'))

        path = 'web/deviceinfo'
        deviceinfo = self.fetch(path)
        message('device info is {}'.format(str(deviceinfo)))
        parse_device_info(deviceinfo)

    def bouquets(self):
        """
        Get bouquets. If no bouquets exist in the database, or the database query
        fails then just get the bouquets from the reciever.
        """

        def get_bouquets():


            path = 'web/getservices'
            try:
                bouquet_xml = self.fetch(path=path)
                bouquets = parse_bouquets(bouquet_xml)
                bouquets = filter(lambda x : LAST_SCANNED  not in x.values(), bouquets)
                message('bouquests fetched from database is {}'.format(str(bouquets)))
                if bouquets:
                    self.db.insert('Bouquet', bouquets)
                    #TODO Could do with raising a custome exception here...
            except Exception as e:
                message('Error fetching bouquets from receiver. Exception was {}'.format(str(e)))

        def parse_bouquets( bouquet_xml):

            return map(lambda x: self.get_names(x),
                       Soup(bouquet_xml).findAll('e2service'))

        try:
            rows =  self.db.get('Bouquet')
            return self.check_rows(rows, self.bouquets, get_bouquets)
            #message(rows)
            #if rows:
            #    message('returning rows {}'.format(str(rows)))
            #    return rows
            #else:
            #    message('No bouquets found so I am calling the receiver')
            #    get_bouquets()
            #    self.bouquets()
        except Exception as e:
            message(e)
            get_bouquets()
            self.bouquets()

    def channels(self, where=None):
        """
        Get channels. If no channels exist in the database, or the database query
        fails then get the channels from the reciever.
        """

        def get_channels():

            path = 'web/getservices'
            bouquet = self.bouquets()
            bouquet = bouquet if bouquet else []
            channels_xml = map(lambda b: (b['service_reference'],self.fetch(path, {'sRef': b['service_reference']})), bouquet)
            channels = parse_channels(channels_xml)
            self.db.insert('Channel', channels)

        def parse_channels(channel_xml):

            channels = []
            for b, channel in channel_xml:

                s = Soup(channel).findAll('e2service')
                if s:
                    a = map(lambda x: self.get_names(x), s)
                    d = [c.update({'bo_id': b}) for c in a]
                    channels.extend(a)

            return channels

        try:
            rows = self.db.get('Channel', where=where)
            return self.check_rows(rows, self.channels, get_channels)

            #if rows:
            #    message('Returning rows {}'.format(str(rows)))
            #    return rows
            #else:
            #    message('No channels found  so I am calling the receiver')
            #    get_channels()
            #    self.channels()
        except:
            get_channels()
            self.channels()

    def check_rows(self, rows, sender_function, callback):

        if rows:
            message('Returning rows for function {}'.format(str(sender_function.__name__)))
            return rows
        else:
            message('Unable to  find any rows in database invoking {} , so calling the receiver using {}'.format(str(sender_function.__name__), str(callback.__name__)))
            callback()
            sender_function()

    def events(self, update=False, where = None):
        """
        Get events. First, for all the events in the database, get the lowest(earliest time)
        of all the maximum event start times for each channel. This will prevent us from having gaps
        in the events that we have on a specific channel.
        We then get all the channels, and get all the events after a given start time. If the start time
        is unable to be calculated, then just fetch all the events for each channels
        """

        earliest_start_time = self.db.raw_sql(EARLIEST_STAR_TIME)
        channels = self.channels()

        try:
            start_time = earliest_start_time[0][0]
        except :
            start_time = 0

        try:
            if update:
                self.get_events(start_time, channels)

            rows = self.db.get('Events', where=where)
            return self.check_rows(rows, self.events, self.get_events)

        except:
            self.get_events()
            self.events()

    def get_events(self, earliest_start_time=None, channels=None):

        path = 'web/epgservice'
        channels = self.db.get('Channel')
        events = []
        for channel in channels:
            event_xml = [(channel['service_reference'], self.fetch(path, {'sRef': channel['service_reference'], 'time': earliest_start_time}))]
            event = self.parse_events(event_xml)
            events.extend(event)
        self.db.insert('Event', filter(None, events))

    def current(self):

        def get_current():

            path = 'web/getcurrent'
            current = self.fetch(path)
            return parse_current(current)

        def parse_current( current):

            event_soup = Soup(str(current))
            current_service  = event_soup.find('e2currentserviceinformation')
            sref = current_service.find('e2servicereference').text
            event_xml = [(sref, current)]

            event = self.parse_events(event_xml)[0]
            name = current_service.find('e2servicename').text
            event['sref'] =sref
            event['service_name'] = name

            return event
        event = get_current()

        return event

    def create_event(self, event_xml):

        try:
            event_soup = Soup(str(event_xml))
            event_details = {
                             'event_title': escape(event_soup.find('e2eventtitle').text),
                             'event_description': escape(event_soup.find('e2eventdescription').text),
                             'event_description_extended': escape(event_soup.find('e2eventdescriptionextended').text),
                             'event_start': int(event_soup.find('e2eventstart').text),
                             'event_duration': int(event_soup.find('e2eventduration').text),
                             'event_id': int(event_soup.find('e2eventid').text)
                             }
            return event_details
        except Exception as e:
            return None


    def event_now(self):
        """
        Gets the current event for each channel, and stores then in the database
        """

        try:
            channels = self.db.get('Channel')
            rows = self.db.get('NowNext')
            message('Now next rows is {}'.format(str(rows)))
            if len(rows) > len(channels) / 2:
                message('Returning rows {}'.format(str(rows)))
                return rows
            else:
                message('No or not enough now events found  so I am calling the receiver')
                path = 'web/epgservicenow'
                channels = self.db.get('Channel')
                events = []
                for channel in channels:
                    event_xml = [(channel['service_reference'], self.fetch(path, {'sRef': channel['service_reference']}))]
                    event = self.parse_events(event_xml)

                    events.extend(event)
                self.db.insert('Event', filter(None, events))
                self.event_now()
        except BaseException as e:
            message(e)
            pass

    def event_next(self):
        """
        Gets the next event for each channel, and stores then in the database. Really we only want to do this when we
        initially start using the database, rather than loading all the events in one go, just to get us started.
        Further
        """
        try:
            channels = self.db.get('Channel')
            rows = self.db.get('NowNext')
            if len(rows) > len(channels) / 1.5:
                message('Returning rows {}'.format(str(rows)))
                return rows
            else:
                message('No or not enough next events found  so I am calling the receiver')
                path = 'web/epgservicenext'
                channels = self.db.get('Channel')
                events = []
                for channel in channels:
                    event_xml = [(channel['service_reference'], self.fetch(path, {'sRef': channel['service_reference']}))]
                    event = self.parse_events(event_xml)
                    events.extend(event)
                self.db.insert('Event', filter(None, events))
                self.event_next()
        except:
            pass

    def parse_events(self, event_xml):
        events = []
        for b, event in event_xml:

            s = Soup(event).findAll('e2event')
            if s:
                a = map(lambda x: self.create_event(x), s)

                d = [c.update({'ch_id': b}) for c in a if c]
                events.extend(a)

        return events

    @staticmethod
    def get_names(x):
        elements = x.findAll(['e2servicereference', 'e2servicename'])
        return {'service_reference': elements[0].text, 'service_name': elements[1].text}


    def get_channel_epg(self, service_reference=None):

        path = 'web/epgservice'
        for channel in [service_reference] if service_reference else self.channels:
            epg_xml = self.fetch(path, {'sRef': channel.service_reference})


            channel.events = self.parse_channel_epg(epg_xml)

        return None

    def get_multi_epg(self, bouquet_reference=None):

        events = []

        path = 'web/epgmulti'
        for bouquet in [bouquet_reference] if bouquet_reference else self.bouquets:
            epg_xml = self.fetch(path, {'bRef': bouquet.service_reference})
            events.append(self.parse_channel_epg(epg_xml))


        return None



    def parse_channel_epg(self, epg_xml):

        #get each event xml
        events = Soup(epg_xml).findAll('e2event')

        return [self.create_event(event) for event in events]





    def fetch(self, path='', data=None):
        """
        Fetch data from the receiver
        """
        req = Http(timeout=60)
        headers = []

        url = 'http://{}:{}/{}'.format(self.host, self.port, path)
        try:
            if data:
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                resp, content = req.request(url, "POST", headers=headers, body=urlencode(data))
            else:
                resp, content = req.request(url, "GET", data)
        except:
            raise
        return content

dev = 1
r = Receiver()

r.setup(host='192.168.1.252', port=80)
print r.current()
#r.event_now()


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


# TODO Returning the wrong result when eventid was incorrectly named. eventID
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
    #TODO May not be getting audio correct after update to HTTPlib2
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
        print soup
        state = soup[0].e2result.string
        print state
        if state == '	Success':
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

##############################################################
# Send a power signal to the box                             #
##############################################################
def set_power_state(host=None, web=None, state=0):
    import socket
    result = False
    error = None
    try:
        url = 'http://{}:{}/web/powerstate'.format(host, web)
        data = {'newstate': state}
        soup = get_data((url, data))
        if 'false' in soup[0].e2instandby.string:
            result = True
            error = 0
        else:
            result = False
            error = 0
    except socket.error as e:

        if e.errno:
            print e.errno
            print e.message
            print e.args
            if int(e.errno) == 10054:  # 1, 2 returns 0054
                result = True
                if state == 1:
                    error = 1
                elif state == 2:
                    error = 2
                else:
                    error = 3
            if int(e.errno) == 10061:  # 3  return 0061
                result = True
                error = 4  # stil restarting
        else:
            #Unable to connect - Timed out
            return True, e.args[0]
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
                    'zxz': '%2B',
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
    #TODO Pass in a timeout value here
    from httplib2 import Http
    from urllib import urlencode
    req = Http(timeout=10)
    results = []
    for item in args:
        u = item[0]
        data = item[1]
        print data
        try:
            if data:
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                resp, content = req.request(u, "POST", headers=headers, body=urlencode(data))
                print resp, content
            else:
                resp, content = req.request(u, "GET", data)
            soup = Soup(content)
            results.append(soup)
        except:

            raise
    return results


def split_folders(name, folders_files, path):
    folder = []
    for f in folders_files.keys():
        try:
            if name == 'nt':
                #Need to remove the initial path here
                parts = f.split(path).pop().rstrip(' /\\').lstrip(' /\\')

            else:
                print build_move_path
                print len(path)
                parts = f[len(path) +1:]
            if parts != '':
                folder.append(parts)
        except:
            pass
    return folder


def get_folder_contents(name, movie_path, folders_files, folder_contents):
    if name == 'nt':
        separator = '\\'
    else:
        separator = '/'
    full_path = '{}{}{}'.format(movie_path, separator, folder_contents)

    return folders_files.get(full_path)


def get_movie_subfolders(host=None, path='\Harddisk\movie', merge=False, folders=False, folder_contents=None):

    import re
    import fnmatch

    movie_path = build_move_path(host, path)
    name = os.name
    includes = ['*.mp4', '*.ts', '*.avi', '*.mpg', '*.mpeg', '*.webm', '*.x264', 'mkv' ]
    includes = r'|'.join([fnmatch.translate(x) for x in includes])
    pattern = '^(.*?\\.(\\bTrash\\b)[$]*)$' # To exclude the trash folder
    folders_files = {}

    #first see if we have a request for multiple folders
    multiples = path.split(',')
    if len(multiples) > 1:
        #we have passed in multiple folders
        pass
    else:
        #we have passed in just root
        try:
            print 'movie path is {}'.format(movie_path)
            for root, folder, files in os.walk(movie_path):
                #exclude trash and sub folders with no files
                if not re.match(pattern, root, 0):
                    if len(files) > 0:
                        folders_files[root] = ([f for f in files if re.match(includes, f)])
        except:
            print 'Error'
            raise
        if folders:
            folder = split_folders(name, folders_files, path)
            return folder
        if merge:
            # Just return the merged file list - all in one location
            return list(chain(*folders_files.values()))
        if folder_contents:
            return get_folder_contents(name, movie_path, folders_files, folder_contents)
        else:
            #return files in their folders
            return folders_files



def build_move_path(host=None, path=None):

    #set correct separators
    name = os.name
    separator = '\\'  # need to escape

    if path:
        path.lstrip('\\/').rstrip('\\/').lstrip('/').rstrip('/')
        parts = path.split(separator)
        if '/' in path:
            separator = '/'
            parts = path.split(separator)
        parts = [x if len(x) > 1 else None for x in parts]
        print parts
        if parts[0] != host and name == 'nt':
            parts.insert(0, host)
        # now build the path
        fullpath = ''
        if name == 'nt':
            fullpath = fullpath.join('\\')
        for f in parts:
            if f:
                fullpath = fullpath + separator + f
        return fullpath
    return None

# Stuff here actually gets loaded by the server, so remember if things start going wierd


