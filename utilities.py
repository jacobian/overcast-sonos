"""
Utility functions.

Little utility functions to help you along :)
"""

import requests
import logging

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

# turns a string like 'Feb 24 - 36 min left' into seconds


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


def final_redirect_url(url):
    redirected_url = requests.head(url, allow_redirects=True).url
    if url != redirected_url:
        log.debug('''Redirected url '%s' to '%s'.''', url, redirected_url)
    return redirected_url
