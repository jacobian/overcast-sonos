"""
An overcast "API".

Overcast doesn't really offer an official API, so this just sorta apes it.
"""

import requests
import lxml.html
import urlparse
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('overcast-sonos')

class Overcast(object):

    def __init__(self, email, password):
        self.session = requests.session()
        r = self.session.post('https://overcast.fm/login', {'email': email, 'password': password})
        doc = lxml.html.fromstring(r.content)
        alert = doc.cssselect('div.alert')
        if alert:
            raise Exception("Can't login: {}".format(alert[0].text_content().strip()))

    def _get_html(self, url):
        return lxml.html.fromstring(self.session.get(url).content)

    def get_active_episodes(self):
        doc = self._get_html('https://overcast.fm/podcasts')
        return [
            self.get_episode_detail(cell.attrib['href'])
            for cell in doc.cssselect('a.episodecell')
            if 'href' in cell.attrib
        ]

    def get_episode_detail(self, episode_id):
        episode_href = urlparse.urljoin('https://overcast.fm', episode_id)
        doc = self._get_html(episode_href)

        time_elapsed_seconds = int(doc.cssselect('audio#audioplayer')[0].attrib['data-start-time'])
        time_remaining_seconds = self.get_episode_time_remaining_seconds(episode_id, doc)
        duration = time_elapsed_seconds + time_remaining_seconds
        if time_elapsed_seconds == duration:
            duration = 0

        return {
            'id': episode_href.lstrip('/'),
            'title': doc.cssselect('div.titlestack div.title')[0].text_content(),
            'podcast_title': doc.cssselect('div.titlestack div.caption2 a')[0].text_content(),
            'offsetMillis': time_elapsed_seconds * 1000,
            'duration': duration,
            'albumArtURI': doc.cssselect('div.fullart_container img')[0].attrib['src'],
            'audio_uri': doc.cssselect('audio#audioplayer source')[0].attrib['src'],
            'audio_type': doc.cssselect('audio#audioplayer source')[0].attrib['type'],
        }

    def get_episode_time_remaining_seconds(self, episode_id, episode_html):
        log.debug('''getting the remaining time. episode id is %s''', episode_id)
        podcast_id = episode_html.cssselect('div.titlestack div.caption2 a')[0].attrib['href']
        podcast_href = urlparse.urljoin('https://overcast.fm', podcast_id)
        doc = self._get_html(podcast_href)
        time_remaining_seconds = 0

        for cell in doc.cssselect('a.extendedepisodecell'):
            if episode_id in cell.attrib['href']:
                cell.cssselect('div.caption2')[0].text_content()
                unparsed_time_remaining = cell.cssselect('div.singleline')[1].text_content()
                time_remaining_seconds = self.duration_in_seconds(unparsed_time_remaining)
                break

        return time_remaining_seconds

    def duration_in_seconds(self, str):
        seconds = 0
        try:
            strings = str.split(' ')
            for string in strings:
                if ":" in string:
                    list = string.split(":")
                    list.reverse()
                    for i,x in enumerate(list):
                        seconds += int(x) * (60**i)
                    break
        except:
            log.debug('''Couldn't parse the episode's duration in seconds from the string %s.''', str)
            pass

        log.debug('''Parsed the episode's duration in seconds from the string %s -> %d''', str, seconds)

        return seconds

    def get_all_podcasts(self):
        doc = self._get_html('https://overcast.fm/podcasts')
        return [
            {'id': cell.attrib['href'].lstrip('/'),
            'title': cell.cssselect('div.title')[0].text_content(),
            'albumArtURI': cell.cssselect('img')[0].attrib['src'],
            }
            for cell in doc.cssselect('a.feedcell')
            if 'href' in cell.attrib
        ]

    def get_all_podcast_episodes(self, podcast_id, limit=10):
        """
        get all episodes (played or not) for a podcast.

        needs to be limited to avoid hammering overcast and timing out sonos.
        """
        podcast_href = urlparse.urljoin('https://overcast.fm', podcast_id)
        doc = self._get_html(podcast_href)
        return [
            self.get_episode_detail(cell.attrib['href'])
            for cell in doc.cssselect('a.extendedepisodecell')[:limit]
            if 'href' in cell.attrib
        ]