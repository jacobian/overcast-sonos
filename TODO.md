- tests yay
- refactor to be a WSGI app
- convert to username/password auth 
    - http://musicpartners.sonos.com/node/82
    - looks like I'll have to hack the soap dispatcher to somehow save headers :(
- add a picture to the actual Overcast Sonos service

Maybe:

- deploy as an app?
    - this would mean I'd have access to people's overcast passwords....
    
DONE:
- write a README with instructions
- update play status - reportPlaySeconds/Status SOAP call can map to overcast play status XHR
    - not sure how to tell when something's finished to let overcast know, figure that out
- art!
- actually gather episode duration
- resolve redirects to find the actual media URL - sonos doesn't seem to follow redirects
- properly implement getLastUpdate
- refactor getMetadata not to be repetetive and ugly
- load episode lists faster and only call get_episode_detail if absolutely needed
- refactor the way episode_id is used (sometimes with a slash, sometimes without)
- "delete" or remove an episode once it has finished playing (currently it just shows as 00:00 remaining and must be manually finished on some other way)
