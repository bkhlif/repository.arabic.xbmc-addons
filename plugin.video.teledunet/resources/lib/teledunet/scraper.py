import cookielib
import re
import urllib2
from BeautifulSoup import BeautifulSoup
from models import ChannelItem
from hardcode import HARDCODED_STREAMS

#HEADER_REFERER = 'http://www.teledunet.com/'
HEADER_REFERER = 'http://www.teledunet.com/list_chaines.php'
HEADER_HOST = 'www.teledunet.com'
HEADER_USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
TELEDUNET_TIMEPLAYER_URL = 'http://www.teledunet.com/player/?channel=%s'
PPV_CHANNEL_URL='rtmp://5.135.134.110:1935/teledunet/'

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))


def _get(request):
    """Performs a GET request for the given url and returns the response"""
    return opener.open(request).read()

def _html(url):
    """Downloads the resource at the given url and parses via BeautifulSoup"""
    headers = { "User-Agent": HEADER_USER_AGENT  }
    request = urllib2.Request (url , headers = headers)
    return BeautifulSoup(_get(request), convertEntities=BeautifulSoup.HTML_ENTITIES)


def __get_cookie_session():
    # Fetch the main Teledunet website to be given a Session ID
    _html('http://www.teledunet.com')

    for cookie in cj:
        if cookie.name == 'PHPSESSID':
            return 'PHPSESSID=%s' % cookie.value

    raise Exception('Cannot find PHP session from Teledunet')


def __get_channel_time_player(channel_name):
    url = TELEDUNET_TIMEPLAYER_URL % channel_name
    # Set custom header parameters to simulate request is coming from website
    req = urllib2.Request(url)
    req.add_header('Referer', HEADER_REFERER)
    req.add_header('Host', HEADER_HOST)
    req.add_header('User-agent', HEADER_USER_AGENT)
    req.add_header('Cookie', __get_cookie_session())

    html = _get(req)
    m = re.search('time_player=(.*);', html, re.M | re.I)
    time_player_str = eval(m.group(1))

    m = re.search('curent_media=\'(.*)\';', html, re.M | re.I)
    if 'bein_sport' in channel_name:
        rtmp_url=PPV_CHANNEL_URL+channel_name
    else:
        rtmp_url = m.group(1)
    play_path = rtmp_url[rtmp_url.rfind("/") + 1:]
    return rtmp_url, play_path, repr(time_player_str).rstrip('0').rstrip('.')


def get_rtmp_params(channel_name):
    rtmp_url, play_path, time_player_id = __get_channel_time_player(channel_name)

    return {
        'rtmp_url': rtmp_url,
        'playpath': play_path,
        'app': 'teledunet',
        'swf_url': ('http://www.teledunet.com/player.swf?'
                    'id0=%(time_player)s&'
                   ) % {'time_player': time_player_id, 'channel_name': play_path, 'rtmp_url': rtmp_url},
        'video_page_url': 'http://www.teledunet.com/player/?channel=%s' % play_path,
        'live': '1'
    }

def get_channels():
    html = _html(HEADER_REFERER)
    channel_divs = lambda soup : soup.findAll("div", { "class" : re.compile("div_channel") })
    channels = [ChannelItem(el=el) for el in channel_divs(html)]

    # Extend Teledunet list with custom hardcoded list created by community
    channels.extend(__get_hardcoded_streams())
    return channels


def __get_hardcoded_streams():
    return [ChannelItem(json=json) for json in HARDCODED_STREAMS]


def debug():
    print len(get_channels())
    #print __get_channel_time_player('2m')
    #print get_rtmp_params('2m')
    pass


if __name__ == '__main__':
    debug()
