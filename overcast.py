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
            
    def get_active_episodes(self):
        r = self.session.get('https://overcast.fm/podcasts')
        doc = lxml.html.fromstring(r.content)
        return [
            self.get_episode_detail(cell.attrib['href'])
            for cell in doc.cssselect('a.episodecell')
            if 'href' in cell.attrib
        ]
        
    def get_episode_detail(self, episode_id):
        episode_href = urlparse.urljoin('https://overcast.fm', episode_id)
        r = self.session.get(episode_href)
        doc = lxml.html.fromstring(r.content)
        return {
            'id': episode_href.rsplit('/', 1)[-1],
            'title': doc.cssselect('div.titlestack div.title')[0].text_content(),
            'podcast_title': doc.cssselect('div.titlestack div.caption2 a')[0].text_content(),
            'duration':  60, # fixme - fuck where do I get the duration from :(
            'audio_uri': doc.cssselect('audio#audioplayer source')[0].attrib['src'],
            'audio_type': doc.cssselect('audio#audioplayer source')[0].attrib['type'],
        }
            