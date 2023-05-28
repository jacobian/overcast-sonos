"""
Utility functions.

Little utility functions to help you along :)
"""

import requests
import logging
import re
from datetime import datetime

log = logging.getLogger('overcast-sonos')

# Turns a string like 'Feb 24 - 36 min left' into seconds
def duration_in_seconds(str):
    seconds = -1
    try:
        strings = str.split()
        if 'at' in strings:
            log.debug('Duration could not be determined because Overcast is giving the start time instead of time left')
            return seconds
        else:
            minuteIndex = strings.index('min') - 1
            seconds = int(strings[minuteIndex]) * 60
            log.debug('''Parsed the episode's duration in seconds from the string %s -> %d''', str, seconds)
            return seconds
    except:
        log.debug('''Couldn't parse the episode's duration in seconds from the string %s.''', str)
        return seconds


# Works out the final URL for those podcast platforms that redirect to another URL
# If the redirected URL has a #t= timecode in it, we remove this as the Sonos player can't play these back, and it fixes compatibility with requests 2.19 and higher
def final_redirect_url(url):
    redirected_url = requests.head(url, allow_redirects=True).url
    if url != redirected_url:
        log.debug('''Redirected url '%s' to '%s'.''', url, redirected_url)
    
    # for certain podcasts, the '#=' is added to the audio URL which causes Sonos to fail to connect
    regex='#t=[0-9]*$'
    if re.search(regex, redirected_url):
        log.debug('Truncating the \'#t=\' part of the audio URL.')
        redirected_url = re.sub(regex, '', redirected_url)

    return redirected_url

# Turns a string like 'Dec 2, 2020 • 171 min' or 'Jan 13 • 147 min' into a date
# Sets a default date in case it can't parse it of 2000-01-01
def convert_release_date(str):
    final_date = '2000-01-01T00:00:00'
    try:
        strings = str.split('•')
        strdate = strings[0]
        strdate = strdate.replace(' ','')
        strdate = strdate.replace('\n','')
        if ',' in strdate:
            date = datetime.strptime(strdate, '%b%d,%Y')
            final_date = date.isoformat()
        else:
            thisyear = datetime.now().year
            date = datetime.strptime(strdate, '%b%d')
            date = date.replace(year=thisyear)
            final_date = date.isoformat()
    except:
        pass

    return final_date
