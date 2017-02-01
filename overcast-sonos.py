import os
import logging
import uuid
from overcast import Overcast, utilities
from pysimplesoap.server import SoapDispatcher, SOAPHandler
from BaseHTTPServer import HTTPServer

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('overcast-sonos')

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


def getMetadata(id, index, count):
    log.debug('at=getMetadata id=%s index=%s count=%s', id, index, count)

    if id == 'root':
        response = {'getMetadataResult': [
            {'index': 0, 'count': 2, 'total': 2},
            {'mediaCollection': {
                'id': 'episodes',
                'title': 'All Active Episodes',
                'itemType': 'container',
                'canPlay': False,
                'albumArtURI': 'http://is2.mzstatic.com/image/thumb/Purple62/v4/22/c7/93/22c793a7-55a8-e72b-756c-90641e7b96d4/source/175x175bb.jpg',
            }},
            {'mediaCollection': {
                'id': 'podcasts',
                'title': 'Podcasts',
                'itemType': 'container',
                'canPlay': False,
                'albumArtURI': 'http://is2.mzstatic.com/image/thumb/Purple62/v4/22/c7/93/22c793a7-55a8-e72b-756c-90641e7b96d4/source/175x175bb.jpg',
            }},
        ]}

    elif id == 'episodes':
        all_episodes = overcast.get_active_episodes()
        episodes = all_episodes[index:index+count]
        response = {'getMetadataResult': [{'index': index, 'count': len(episodes), 'total': len(all_episodes)}]}
        for episode in episodes:
            response['getMetadataResult'].append({
                'mediaMetadata': {
                    'id': 'episodes/' + episode['id'],
                    'title': episode['title'],
                    'mimeType': episode['audio_type'],
                    'itemType': 'track',
                    'trackMetadata': {
                        'artist': episode['podcast_title'],
                        'albumArtist': episode['podcast_title'],
                        'albumArtURI': episode['albumArtURI'],
                        'genreId': 'podcast',
                        'canResume': True,
                    }
                }
            })

    elif id == 'podcasts':
        all_podcasts = overcast.get_all_podcasts()
        podcasts = all_podcasts[index:index+count]
        response = {'getMetadataResult': [{'index': index, 'count': len(podcasts), 'total': len(all_podcasts)}]}
        for podcast in podcasts:
            response['getMetadataResult'].append({'mediaCollection': {
                'id': 'podcasts/' + podcast['id'],
                'title': podcast['title'],
                'albumArtURI': podcast['albumArtURI'],
                'itemType': 'container',
                'canPlay': False,
            }})

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
    args={'id': str, 'index': int, 'count': int}
)

###


def getMediaMetadata(id):
    log.debug('at=getMediaMetadata id=%s', id)
    _, episode_id = id.rsplit('/', 1)
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
    log.debug('at=getMediaMetadata response=%s', response)
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
    return {'reportPlaySecondsResult': {'interval': 30}}


dispatcher.register_function(
    'reportPlaySeconds', reportPlaySeconds,
    returns={'reportPlaySecondsResult': {'interval': int}},
    args={'id': str, 'seconds': int, 'offsetMillis': int, 'contextId': str}
)


def reportPlayStatus(id, status, contextId, offsetMillis):
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
    httpd = HTTPServer(("", 8140), SOAPHandler)
    httpd.dispatcher = dispatcher
    httpd.serve_forever()
