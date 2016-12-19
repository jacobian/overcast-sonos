"""
An overcast "API".

Overcast doesn't really offer an official API, so this just sorta apes it.
"""

import requests
import lxml.html
import urlparse

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
        return {
            'id': episode_href.lstrip('/'),
            'title': doc.cssselect('div.titlestack div.title')[0].text_content(),
            'podcast_title': doc.cssselect('div.titlestack div.caption2 a')[0].text_content(),
            'duration':  60, # fixme - fuck where do I get the duration from :(
            'audio_uri': doc.cssselect('audio#audioplayer source')[0].attrib['src'],
            'audio_type': doc.cssselect('audio#audioplayer source')[0].attrib['type'],
        }
    
    def get_all_podcasts(self):
        doc = self._get_html('https://overcast.fm/podcasts')
        return [
            {'id': cell.attrib['href'].lstrip('/'), 'title': cell.cssselect('div.title')[0].text_content()}
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
