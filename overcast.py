"""
An overcast "API".

Overcast doesn't really offer an official API, so this just sorta apes it.
"""

import requests
import lxml.html
import urlparse
import utilities
import logging
import threading

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

    def get_active_episodes(self, get_details=False):
        active_episodes = []
        active_episodes_dictionary = {}
        doc = self._get_html('https://overcast.fm/podcasts')
        for index, cell in enumerate(doc.cssselect('a.episodecell')):
            if 'href' in cell.attrib:
                if get_details:
                    episode_id = cell.attrib['href']
                    time_remaining_seconds = self.get_episode_time_remaining_seconds_from_episode_cell(cell, False)
                    t = threading.Thread(target=self.add_episode_detail_to, args=(active_episodes_dictionary, index, episode_id, time_remaining_seconds))
                    t.setDaemon(True)
                    t.start()
                else:
                    active_episodes.append({
                        'id': urlparse.urljoin('https://overcast.fm', cell.attrib['href']).lstrip('/'),
                        'title': cell.cssselect('div.titlestack div.title')[0].text_content(),
                        'audio_type': 'audio/mpeg',
                        'podcast_title': cell.cssselect('div.titlestack div.caption2')[0].text_content(),
                        'albumArtURI': cell.cssselect('img')[0].attrib['src'],
                        'duration': -1,
                    })
    
        main_thread = threading.currentThread()
        for t in threading.enumerate():
            if t is not main_thread:
                log.debug('''Joining on thread %s''', t.getName())
                t.join()

        if not active_episodes:
            active_episodes = [active_episodes_dictionary[key] for key in sorted(active_episodes_dictionary)]

        return active_episodes

    def add_episode_detail_to(self, ordered_episodes, key, episode_id, time_remaining_seconds=None):
        ordered_episodes[key] = self.get_episode_detail(episode_id, time_remaining_seconds)

    def get_episode_detail(self, episode_id, time_remaining_seconds=None):
        episode_href = urlparse.urljoin('https://overcast.fm', episode_id)
        doc = self._get_html(episode_href)

        time_elapsed_seconds = int(doc.cssselect('audio#audioplayer')[0].attrib['data-start-time'])
        time_remaining_seconds = time_remaining_seconds or self.get_episode_time_remaining_seconds(episode_id, doc)
        duration = time_elapsed_seconds + time_remaining_seconds
        if time_elapsed_seconds == duration:
            duration = -1

        return {
            'id': episode_href.lstrip('/'),
            'title': doc.cssselect('div.titlestack div.title')[0].text_content(),
            'podcast_title': doc.cssselect('div.titlestack div.caption2 a')[0].text_content(),
            'offsetMillis': time_elapsed_seconds * 1000,
            'duration': duration,
            'data_item_id': doc.cssselect('audio#audioplayer')[0].attrib['data-item-id'],
            'data_sync_version': doc.cssselect('audio#audioplayer')[0].attrib['data-sync-version'],
            'albumArtURI': doc.cssselect('div.fullart_container img')[0].attrib['src'],
            'parsed_audio_uri': doc.cssselect('audio#audioplayer source')[0].attrib['src'],
            'audio_type': doc.cssselect('audio#audioplayer source')[0].attrib['type'],
            'delete_episode_uri': doc.cssselect('a#delete_episode_button')[0].attrib['href']
        }

    def get_episode_time_remaining_seconds(self, episode_id, episode_html):
        log.debug('''getting the remaining time. episode id is %s''', episode_id)
        podcast_id = episode_html.cssselect('div.titlestack div.caption2 a')[0].attrib['href']
        podcast_href = urlparse.urljoin('https://overcast.fm', podcast_id)
        doc = self._get_html(podcast_href)

        for cell in doc.cssselect('a.extendedepisodecell'):
            if episode_id in cell.attrib['href']:
                return self.get_episode_time_remaining_seconds_from_episode_cell(cell, True)

    def get_episode_time_remaining_seconds_from_episode_cell(self, cell, is_extended_cell):
        unparsed_time_remaining_index = 1 if is_extended_cell else 2
        unparsed_time_remaining = cell.cssselect('div.singleline')[unparsed_time_remaining_index].text_content()
        time_remaining_seconds = utilities.duration_in_seconds(unparsed_time_remaining)
        return time_remaining_seconds

    def get_all_podcasts(self):
        doc = self._get_html('https://overcast.fm/podcasts')
        return [
            {
                'id': cell.attrib['href'].lstrip('/'),
                'title': cell.cssselect('div.title')[0].text_content(),
                'albumArtURI': cell.cssselect('img')[0].attrib['src'],
            }
            for cell in doc.cssselect('a.feedcell')
            if 'href' in cell.attrib
        ]

    def get_all_podcast_episodes(self, podcast_id):
        """
        get all episodes (played or not) for a podcast.
        """
        podcast_href = urlparse.urljoin('https://overcast.fm', podcast_id)
        doc = self._get_html(podcast_href)
        albumArtURI = doc.cssselect('img.art')[0].attrib['src']
        podcast_title = doc.cssselect('h2.centertext')[0].text_content()
        return [
            # NOTE: If the hardcoded audio_type causes any problems, just uncomment the line below and comment out the dictionary below it.
            # self.get_episode_detail(cell.attrib['href'])
            {
                'id': urlparse.urljoin('https://overcast.fm', cell.attrib['href']).lstrip('/'),
                'title': cell.cssselect('div.titlestack div.title')[0].text_content(),
                'audio_type': 'audio/mpeg',
                'podcast_title': podcast_title,
                'albumArtURI': albumArtURI,
            }
            for cell in doc.cssselect('a.extendedepisodecell')
            if 'href' in cell.attrib
        ]

    def update_episode_offset(self, episode, updated_offset_seconds):
        log.debug("updated_offset_seconds = %d and duration = %d", updated_offset_seconds, episode['duration'])
        url = 'https://overcast.fm/podcasts/set_progress/' + episode['data_item_id']
        params = {'p': updated_offset_seconds, 'speed': 0, 'v': episode['data_sync_version']}
        log.debug('Updating offset of episode with id %s to %d', episode['id'], updated_offset_seconds)
        self.session.post(url, params)
        if updated_offset_seconds >= episode['duration']:
            self.delete_episode(episode)

    def delete_episode(self, episode):
        url = 'https://overcast.fm' + episode['delete_episode_uri']
        log.debug('Deleting episode with id %s', episode['id'])
        self.session.post(url)
