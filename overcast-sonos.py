import os
import logging
import uuid
import podsearch
from overcast import Overcast, utilities
from pysimplesoap.server import SoapDispatcher, SOAPHandler
from http.server import HTTPServer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('overcast-sonos')

list_active_episodes_in_root = True
allow_all_active_episodes_as_playlist = True
default_album_art_uri = 'http://is3.mzstatic.com/image/thumb/Purple111/v4/20/5b/5e/205b5ef7-ee0e-7d0c-2d11-12f611c579f4/source/175x175bb.jpg'

class customSOAPHandler(SOAPHandler):

    def do_GET(self):
        log.debug('PATH ==> %s', self.path)
        if self.path == '/presentation_map':
            self.send_response(200)
            self.send_header('Content-type', 'text/xml')
            self.end_headers()
            self.wfile.write('''<?xml version="1.0" encoding="UTF-8"?>
            <Presentation>
                <PresentationMap type="DisplayType">
                    <RootNodeDisplayType>
                        <DisplayMode>LIST</DisplayMode>
                    </RootNodeDisplayType>
                </PresentationMap>
                <PresentationMap type="QuickSkips">
                    <QuickSkip type="episode.podcast" forwardSeconds="45" backwardSeconds="10"/>
                </PresentationMap>
            </Presentation>
            '''.encode("utf-8"))
            log.info('presentation_map has been sent')
            return
        else:
            return SOAPHandler.do_GET(self)


dispatcher = SoapDispatcher('overcast-sonos',
                            location='http://localhost:8140/',
                            namespace='http://www.sonos.com/Services/1.1',
                            trace=True,
                            debug=True
                            )

overcast = Overcast(os.environ['OVERCAST_USERNAME'], os.environ['OVERCAST_PASSWORD'])

mediaCollection = {'id': str,
                   'title': str,
                   'itemType': str,
                   'artistId': str,
                   'artist': str,
                   'albumArtURI': str,
                   'canPlay': bool,
                   'canEnumerate': bool,
                   'canAddToFavorites': bool,
                   'canScroll': bool,
                   'canSkip': bool}

positionInformation = {'id': str,
                       'index': int,  # always 0, "reserved for future use" by Sonos
                       'offsetMillis': int}

trackMetadata = {'artist': str,
                 'albumArtist': str,
                 'albumArtURI': str,
                 'genreId': str,
                 'duration': int,
                 'canResume': bool}

mediaMetadata = {'id': str,
                 'title': str,
                 'mimeType': str,
                 'itemType': str,
                 'trackMetadata': trackMetadata}

###


def getSessionId(username, password):
    log.debug('at=getSessionId username=%s password=%s', username, password)
    return username


dispatcher.register_function(
    'getSessionId', getSessionId,
    returns={'getSessionIdResult': str},
    args={'username': str, 'password': str}
)

###


# Gets metadata for podcasts and episodes, depending on which id is sent from Sonos
def getMetadata(id, index, count, recursive=False):
    log.debug('at=getMetadata id=%s index=%s count=%s recursive=%s', id, index, count, recursive)

# This is the main menu
    if id == 'root':
        response = {'getMetadataResult': []}
        response['getMetadataResult'].append(
            {'mediaCollection': {
                'id': 'podcasts',
                'title': 'Subscribed Podcasts',
                'itemType': 'collection',
                'canPlay': False,
                'albumArtURI': default_album_art_uri,
            }})
        response['getMetadataResult'].append(
                {'mediaCollection': {
                    'id': 'episodes',
                    'title': 'All Active Episodes',
                    'itemType': 'playlist',
                    'canPlay': allow_all_active_episodes_as_playlist,
                    'albumArtURI': default_album_art_uri,
                }})
        if list_active_episodes_in_root:
            all_episodes = overcast.get_active_episodes()
            episodes = all_episodes[index:index+count]
            response['getMetadataResult'].append({'index': index, 'count': len(episodes) + 2, 'total': len(all_episodes) + 2})
            for episode in episodes:
                response['getMetadataResult'].append({
                    'mediaMetadata': {
                        'id': 'episodes/' + episode['id'],
                        'title': episode['title'] + ' - ' + episode['podcast_datetime'].strip(),
                        'mimeType': episode['audio_type'],
                        'itemType': 'track',
                        'semanticType': 'episode.podcast',
                        'trackMetadata': {
                            'artist': episode['title'],
                            'album': episode['title'],
                            'albumArtist': episode['title'],
                            'albumArtURI': episode['albumArtURI'],
                            'genreId': 'podcast',
                            'canResume': True,
                        }
                    }
                })

# This is the display of all episodes when 'All Active Episodes' is selected
    elif id == 'episodes':
        #Temporary fix
        #all_episodes = overcast.get_active_episodes(get_details=True)
        all_episodes = overcast.get_active_episodes(get_details=False)
        episodes = all_episodes[index:index+count]
        response = {'getMetadataResult': [{'index': index, 'count': len(episodes), 'total': len(all_episodes)}]}
        for episode in episodes:
            response['getMetadataResult'].append({
                'mediaMetadata': {
                    'id': 'episodes/' + episode['id'],
                    'title': episode['title'],
                    'mimeType': episode['audio_type'],
                    'itemType': 'track',
                    'semanticType': 'episode.podcast',
                    'trackMetadata': {
                        'artist': episode['title'],
                        'albumArtist': episode['title'],
                        'albumArtURI': episode['albumArtURI'],
                        'genreId': 'podcast',
                        'duration': episode['duration'],
                        'canResume': True,
                    }
                }
            })

# This is the display of all podcasts when 'Podcasts' is selected from the root menu
    elif id == 'podcasts':
        all_podcasts = overcast.get_all_podcasts()
        podcasts = all_podcasts[index:index+count]
        response = {'getMetadataResult': [{'index': index, 'count': len(podcasts), 'total': len(all_podcasts)}]}
        # Sort by name
        podcasts.sort(key=lambda item: item.get("title"))
        for podcast in podcasts:
        # This is crashing on Ubuntu 20.04 for some reason. Will investigate.
        #    if 'itunes' in podcast['id']:
        #        itunesid = podcast['id'].split('/')
        #        itunesid = itunesid[0][6:]
        #        itunesinfo = podsearch.search(itunesid)
        #        print(itunesid)
        #        producer = itunesinfo.author
        #        producer = ''
        #    else:
        #        producer = ''
            response['getMetadataResult'].append({'mediaCollection': {
                'id': 'podcasts/' + podcast['id'],
                'title': podcast['title'],
                'albumArtURI': podcast['albumArtURI'],
                'itemType': 'album',
                'semanticType': 'podcast',
                'canPlay': False,
        #        'producer': producer,
            }})

# This is the display of a single podcasts recent episodes when it is selected from the 'Podcasts' section
    elif id.startswith('podcasts/'):
        podcast_id = id.split('/', 1)[-1]
        all_episodes = overcast.get_all_podcast_episodes(podcast_id)
        episodes = all_episodes[index:index+count]
        response = {'getMetadataResult': [{'index': index, 'count': len(episodes), 'total': len(all_episodes)}]}
        for episode in episodes:
            response['getMetadataResult'].append({
                'mediaMetadata': {
                    'id': 'episodes/' + episode['id'],
                    'title': episode['title'],
                    'mimeType': episode['audio_type'],
                    'itemType': 'track',
                    'semanticType': 'episode.podcast',
                    'summary': episode['summary'],
                    'releasedate': episode['releasedate'],
                    'trackMetadata': {
                        'artist': episode['podcast_title'],
                        'albumArtist': episode['podcast_title'],
                        'albumArtURI': episode['albumArtURI'],
                        'genreId': 'podcast',
                        'canResume': True,
                    }
                }
            })

    else:
        logging.error('unknown getMetadata id id=%s', id)
        response = {'getMetadataResult': [{'index': 0, 'count': 0, 'total': 0}]}

    log.debug('at=getMetadata response=%s', response)
    return response


dispatcher.register_function(
    'getMetadata', getMetadata,
    returns={'getMetadataResult': {'index': int, 'count': int, 'total': int, 'mediaCollection': mediaCollection}},
    args={'id': str, 'index': int, 'count': int, 'recursive': bool}
)

###

# Get the medtadata for a single item/episode
def getMediaMetadata(id):
    log.debug('at=getMediaMetadata id=%s', id)
    _, episode_id = id.rsplit('/', 1)
    log.debug('at=getMediaMetadata episode_id=%s', episode_id)
    episode = overcast.get_episode_detail(episode_id)
    response = {'getMediaMetadataResult': {
        'mediaMetadata': {
            'id': id,
            'title': episode['title'],
            'mimeType': episode['audio_type'],
            'itemType': 'track',
            'trackMetadata': {
                'artist': episode['podcast_title'],
                'albumArtist': episode['podcast_title'],
                'albumArtURI': episode['albumArtURI'],
                'genreId': 'podcast',
                'duration': episode['duration'],
                'canResume': True,
            }
        }
    }}
    log.debug('at=getMediaMetadata response=%s', response)
    return response


dispatcher.register_function(
    'getMediaMetadata', getMediaMetadata,
    returns={'getMediaMetadataResult': mediaMetadata},
    args={'id': str}
)

###


# Get the URI for an episode
def getMediaURI(id):
    log.debug('at=getMediaURI id=%s', id)
    _, episode_id = id.rsplit('/', 1)
    episode = overcast.get_episode_detail(episode_id)
    parsed_audio_uri = episode['parsed_audio_uri']
    audio_uri = utilities.final_redirect_url(parsed_audio_uri)
    response = {'getMediaURIResult': audio_uri,
                'positionInformation': {
                        'id': 'episodes/' + episode['id'],
                        'index': 0,
                        'offsetMillis': episode['offsetMillis']
                    },
                }
    log.debug('at=getMediaURI response=%s', response)
    return response


dispatcher.register_function(
    'getMediaURI', getMediaURI,
    returns={'getMediaURIResult': str, 'positionInformation': positionInformation},
    args={'id': str}
)

###


def getLastUpdate():
    log.debug('at=getLastUpdate')
    return {'getLastUpdateResult': {'catalog': str(uuid.uuid4()), 'favorites': '0', 'pollInterval': 60}}


dispatcher.register_function(
    'getLastUpdate', getLastUpdate,
    returns={'getLastUpdateResult': {'autoRefreshEnabled': bool, 'catalog': str, 'favorites': str, 'pollInterval': int}},
    args={}
)

###


def reportPlaySeconds(id, seconds, offsetMillis, contextId):
    episode_id = id.rsplit('/', 1)[-1]
    log.debug('at=reportPlaySeconds and id=%s, seconds=%d, offsetMillis=%d, contextId=%s, episode_id=%s', id, seconds, offsetMillis, contextId, episode_id)
    episode = overcast.get_episode_detail(episode_id)
    overcast.update_episode_offset(episode, offsetMillis/1000)
    # This was originally set to 30 seconds, but it's been increased to 60 to help prevent rate limiting
    return {'reportPlaySecondsResult': {'interval': 60}}


dispatcher.register_function(
    'reportPlaySeconds', reportPlaySeconds,
    returns={'reportPlaySecondsResult': {'interval': int}},
    args={'id': str, 'seconds': int, 'offsetMillis': int, 'contextId': str}
)


def reportPlayStatus(id, status, offsetMillis, contextId):
    episode_id = id.rsplit('/', 1)[-1]
    log.debug('at=reportPlayStatus and id=%s, status=%s, contextId=%s, offsetMillis=%d, episode_id=%s', id, status, contextId, offsetMillis, episode_id)
    episode = overcast.get_episode_detail(episode_id)
    overcast.update_episode_offset(episode, offsetMillis/1000)


dispatcher.register_function(
    'reportPlayStatus', reportPlayStatus,
    returns={},
    args={'id': str, 'status': str, 'offsetMillis': int, 'contextId': str}
)


def setPlayedSeconds(id, seconds, offsetMillis, contextId):
    episode_id = id.rsplit('/', 1)[-1]
    log.debug('at=setPlayedSeconds and id=%s, seconds=%d, offsetMillis=%d, contextId=%s, episode_id=%s', id, seconds, offsetMillis, contextId, episode_id)
    episode = overcast.get_episode_detail(episode_id)
    overcast.update_episode_offset(episode, offsetMillis/1000)


dispatcher.register_function(
    'setPlayedSeconds', setPlayedSeconds,
    returns={},
    args={'id': str, 'seconds': int, 'offsetMillis': int, 'contextId': str}
)


if __name__ == '__main__':
    log.info('at=start')
    httpd = HTTPServer(("", 8140), customSOAPHandler)
    httpd.dispatcher = dispatcher
    httpd.serve_forever()
