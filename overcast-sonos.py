import os
import logging
from overcast import Overcast
from pysimplesoap.server import SoapDispatcher, SOAPHandler
from BaseHTTPServer import HTTPServer

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger('overcast-sonos')

dispatcher = SoapDispatcher('overcast-sonos',
    location = 'http://localhost:8080/',
    namespace = 'http://www.sonos.com/Services/1.1',
    trace = True,
    debug = True
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

trackMetadata = {'artist': str,
                 'albumArtist': str,
                 'genreId': str,
                 'duration': int}

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
    returns = {'getSessionIdResult': str},
    args = {'username': str, 'password': str}
)

###

def getMetadata(id, index, count):
    log.debug('at=getMetadata id=%s index=%s count=%s', id, index, count)
    
    if id == 'root': 
        response = {'getMetadataResult': [
            {'index': 0, 'count': 1, 'total': 1},
            {'mediaCollection': {
                'id': 'episodes',
                'title': 'All Active Episodes',
                'itemType': 'container',
                'canPlay': False 
            }},
            # {'mediaCollection': {
            #     'id': 'podcasts',
            #     'title': 'Podcasts',
            #     'itemType': 'container',
            #     'canPlay': False 
            # }},
        ]}

    elif id == 'episodes':
        episodes = overcast.get_active_episodes()
        response = {'getMetadataResult': [{'index': 0, 'count': len(episodes), 'total': len(episodes)}]}
        for episode in episodes:
            response['getMetadataResult'].append({'mediaMetadata': {
                'id': 'episodes/' + episode['id'],
                'title': episode['title'],
                'mimeType': episode['audio_type'],
                'itemType': 'track',
                'trackMetadata': {
                    'artist': episode['podcast_title'],
                    'albumArtist': episode['podcast_title'],
                    'genreId': 'podcast',
                    'duration': episode['duration'],
                }
            }})
    
    else:
        logging.error('unknown getMetadata id id=%s', id)
        response = {'getMetadataResult': [{'index': 0, 'count': 0, 'total': 0}]}

    log.debug('at=getMetadata response=%s', response)
    return response

dispatcher.register_function(
    'getMetadata', getMetadata,
    returns = {'getMetadataResult': {'index': int, 'count': int, 'total': int, 'mediaCollection': mediaCollection}},
    args = {'id': str, 'index': int, 'count': int}
)

### 

def getMediaMetadata(id):
    log.debug('at=getMediaMetadata id=%s', id)
    _, episode_id = id.rsplit('/', 1)
    episode = overcast.get_episode_detail(episode_id)
    response = {'getMediaMetadataResult': {'mediaMetadata': {
        'id': id,
        'title': episode['title'],
        'mimeType': episode['audio_type'],
        'itemType': 'track',
        'trackMetadata': {
            'artist': episode['podcast_title'],
            'albumArtist': episode['podcast_title'],
            'genreId': 'podcast',
            'duration': episode['duration'],
        }
    }}}
    log.debug('at=getMediaMetadata response=%s', response)
    return response
    
dispatcher.register_function(
    'getMediaMetadata', getMediaMetadata,
    returns = {'getMediaMetadataResult': mediaMetadata},
    args = {'id': str}
)

###


def getMediaURI(id):
    log.debug('at=getMediaURI id=%s', id)
    _, episode_id = id.rsplit('/', 1)
    episode = overcast.get_episode_detail(episode_id)
    response = {'getMediaURIResult': episode['audio_uri']}
    log.debug('at=getMediaMetadata response=%s', response)
    return response

dispatcher.register_function(
    'getMediaURI', getMediaURI,
    returns = {'getMediaURIResult': str},
     args = {'id': str}
)

###

def getLastUpdate():
    log.debug('at=getLastUpdate')
    return {'getLastUpdateResult': {'catalog': '0', 'favorites': '0', 'pollInterval': 60}}

dispatcher.register_function(
    'getLastUpdate', getLastUpdate,
    returns = {'getLastUpdateResult': {'catalog': str, 'favorites': str, 'pollInterval': int}},
    args = None
)

if __name__ == '__main__':
    log.info('at=start')    
    httpd = HTTPServer(("", 8080), SOAPHandler)
    httpd.dispatcher = dispatcher
    httpd.serve_forever()