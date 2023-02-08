"""
An overcast "API".

Overcast doesn't really offer an official API, so this just sorta apes it.
"""

import requests
import lxml.html
import urllib.parse
import utilities
import logging

log = logging.getLogger('overcast-sonos')
active_episode_prefix = '* '

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

    def get_episode_detail(self, episode_id, time_remaining_seconds=None):
        episode_href = urllib.parse.urljoin('https://overcast.fm', episode_id)
        doc = self._get_html(episode_href)
        audioplayer = doc.cssselect('audio#audioplayer')

        if len(audioplayer) > 0:
            time_elapsed_seconds = int(audioplayer[0].attrib['data-start-time'])
            time_remaining_seconds = time_remaining_seconds or self.get_episode_time_remaining_seconds(episode_id, doc)
            if time_remaining_seconds:
                duration = time_elapsed_seconds + time_remaining_seconds
                if time_elapsed_seconds == duration:
                    duration = -1
            else:
                duration = -1

            return {
                'id': episode_href.lstrip('/'),
                'title': doc.cssselect('div.centertext h2')[0].text_content(),
                'podcast_title': doc.cssselect('div.centertext h3 a')[0].text_content(),
                'offsetMillis': time_elapsed_seconds * 1000,
                'duration': duration,
                'data_item_id': doc.cssselect('audio#audioplayer')[0].attrib['data-item-id'],
                'data_sync_version': doc.cssselect('audio#audioplayer')[0].attrib['data-sync-version'],
                'albumArtURI': doc.cssselect('div.fullart_container img')[0].attrib['src'],
                'parsed_audio_uri': doc.cssselect('audio#audioplayer source')[0].attrib['src'],
                'audio_type': doc.cssselect('audio#audioplayer source')[0].attrib['type'],
                'delete_episode_uri': doc.cssselect('a#delete_episode_button')[0].attrib['href']
            }
        else:
            return None

    def get_episode_time_remaining_seconds(self, episode_id, episode_html):
        log.debug('''getting the remaining time. episode id is %s''', episode_id)
        podcast_id = episode_html.cssselect('div.centertext h3 a')[0].attrib['href']
        podcast_href = urllib.parse.urljoin('https://overcast.fm', podcast_id)
        doc = self._get_html(podcast_href)

        for cell in doc.cssselect('a.extendedepisodecell'):
            if episode_id in cell.attrib['href']:
                return self.get_episode_time_remaining_seconds_from_episode_cell(cell, True)

    def get_episode_time_remaining_seconds_from_episode_cell(self, cell, is_extended_cell):
        unparsed_time_remaining_index = 1 if is_extended_cell else 2
        unparsed_time_remaining = cell.cssselect('div.singleline')[unparsed_time_remaining_index].text_content()
        time_remaining_seconds = utilities.duration_in_seconds(unparsed_time_remaining)
        return time_remaining_seconds

    def get_all_podcasts(self, active_only=False):
        podcasts = []
        doc = self._get_html('https://overcast.fm/podcasts')
        for cell in doc.cssselect('a.feedcell'):
            if 'href' in cell.attrib:
                # perform a check to see if this podcast is active / unplayed
                is_active = len(cell.cssselect('svg.unplayed_indicator')) > 0
                if not active_only or (active_only and is_active):
                    podcasts.append(self.create_podcast_from_cell(cell))

        # sort the result by name
        podcasts.sort(key=lambda item: item.get("title"))

        return podcasts

    def create_podcast_from_cell(self, cell):
        return {
            'id': cell.attrib['href'].lstrip('/'),
            'title': cell.cssselect('div.title')[0].text_content(),
            'albumArtURI': cell.cssselect('img')[0].attrib['src'],
        }

    def get_all_podcast_episodes(self, podcast_id, active_only=False):
        """
        get all episodes (played or not) for a podcast.
        """
        podcast_href = urllib.parse.urljoin('https://overcast.fm', podcast_id)
        doc = self._get_html(podcast_href)
        album_art_uri = doc.cssselect('img.art')[0].attrib['src']
        podcast_title = doc.cssselect('h2.centertext')[0].text_content()

        episodes = []
        for cell in doc.cssselect('a.extendedepisodecell'):
            if 'href' in cell.attrib:
                # check to see if this episode is active / unplayed
                prefix = ''
                if 'usernewepisode' in cell.attrib.get('class', '').split(' '):
                    prefix = active_episode_prefix
                
                # only continue if we are returning all episodes or if we are only returning active ones
                if not active_only or (active_only and prefix != ''):
                    episode_id = urllib.parse.urljoin('https://overcast.fm', cell.attrib.get('href', '')).lstrip('/')
                    episode_title = f"{prefix}{cell.cssselect('div.titlestack div.title')[0].text_content().strip().replace('\n', '')}"
                    summary = cell.cssselect('div.titlestack div.caption2')[0].text_content().strip().replace('\n', '')
                    release_date = utilities.convert_release_date(summary)

                    episodes.append({
                        'id': episode_id,
                        'title': episode_title,
                        'audio_type': 'audio/mpeg',
                        'podcast_title': podcast_title,
                        'albumArtURI': album_art_uri,
                        'summary': summary,
                        'releasedate': release_date
                    })
        return episodes

    def update_episode_offset(self, episode, updated_offset_seconds):
        log.debug("updated_offset_seconds = %d and duration = %d", updated_offset_seconds, episode['duration'])
        url = 'https://overcast.fm/podcasts/set_progress/' + episode['data_item_id']
        params = {'p': updated_offset_seconds, 'speed': 0, 'v': episode['data_sync_version']}
        log.debug('Updating offset of episode with id %s to %d', episode['id'], updated_offset_seconds)
        self.session.post(url, params)
        # Remove episode if less than 60 seconds remaining - due to Overcast not giving us accurate episode lengths we have to do this
        # or we end up with finished episodes still showing in the list
        if updated_offset_seconds >= (episode['duration'] - 60):
            self.delete_episode(episode)

    def delete_episode(self, episode):
        url = 'https://overcast.fm' + episode['delete_episode_uri']
        log.debug('Deleting episode with id %s', episode['id'])
        self.session.post(url)
