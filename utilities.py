"""
Utility functions.

Little utility functions to help you along :)
"""

import requests
import logging
from datetime import datetime

log = logging.getLogger('overcast-sonos')

# We used to look for a 'hh:mm:ss' string and then parse that to seconds, but now overcast only returns minutes :(
# def duration_in_seconds(str):
#     seconds = -1
#     try:
#         strings = str.split(' ')
#         for string in strings:
#             if ":" in string:
#                 list = string.split(":")
#                 list.reverse()
#                 for i, x in enumerate(list):
#                     seconds += int(x) * (60**i)
#                 break
#     except:
#         log.debug('''Couldn't parse the episode's duration in seconds from the string %s.''', str)
#         pass
#
#     log.debug('''Parsed the episode's duration in seconds from the string %s -> %d''', str, seconds)
#
#     return seconds

# Turns a string like 'Feb 24 - 36 min left' into seconds
def duration_in_seconds(str):
    seconds = -1
    try:
        strings = str.split()
        minuteIndex = strings.index('min') - 1
        seconds = int(strings[minuteIndex]) * 60
    except:
        log.debug('''Couldn't parse the episode's duration in seconds from the string %s.''', str)
        pass

    log.debug('''Parsed the episode's duration in seconds from the string %s -> %d''', str, seconds)

    return seconds

# Works out the final URL for those podcast platforms that redirect to another URL
def final_redirect_url(url):
    redirected_url = requests.head(url, allow_redirects=True).url
    if url != redirected_url:
        log.debug('''Redirected url '%s' to '%s'.''', url, redirected_url)
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