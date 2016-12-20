- tests yay
- write a README with instructions
- refactor to be a WSGI app
- convert to username/password auth 
    - http://musicpartners.sonos.com/node/82
    - looks like I'll have to hack the soap dispatcher to somehow save headers :(
- properly implement getLastUpdate
    - by faking this, sonos seems to cache info forever. that's not good.
- refactor getMetadata not to be repetetive and ugly

Maybe:

- deploy as an app?
    - this would mean I'd have access to people's overcast passwords....
    
DONE:
- update play status - reportPlaySeconds/Status SOAP call can map to overcast play status XHR
    - not sure how to tell when something's finished to let overcast know, figure that out
- art!
- actually gather episode duration
- resolve redirects to find the actual media URL - sonos doesn't seem to follow redirects
