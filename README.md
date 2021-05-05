# Play [Overcast](https://overcast.fm/) podcasts on your Sonos.

**Features:**

* Fast!
* Remembers last played position
* Syncs play position back to the Overcast service every 30 seconds or when paused/stopped
* Removes episodes from Overcast when completed

**Limitations:**

* Assumes you've listed to an episode if there is less than 60 seconds remaining, due to Overcast rounding podcast lengths to the nearest minute

**Requirements:**

This should work on any recent version of Python 3. At the time of writing it has been tested on:
 - Python 3.8.5 on Ubuntu 20.04
 - Python 3.9.4 on Manjaro 21.0.3

**Usage:**

1. `pip install -r requirements.txt`

1. `OVERCAST_USERNAME=you@there.com OVERCAST_PASSWORD=1234 python overcast-sonos.py`

1. Go to `http://<SONOS_IP>:1400/customsd.htm`, and enter:

    - SID - some unique SID (255 works if you've not done this before)
    - Service Name - some name, `overcast` works
    - Endpoint URL and Secure Endpoint URL: `http://<YOUR_IP>:8140/overcast-sonos`
    - Presentation map: version = 1 (See below), Uri = `http://<YOUR_IP>:8140/presentation_map`
    - Tick the following:
        - Authentication SOAP header policy: "Anonymous"
        - Container Type: "Music Service"
        - Playback duration logging at track end
        - Playback event logging during track play
        - Disable Alarm Support
        - Disable Multiple Account Support
        - Add play context to reporting
    - Here is an [example screenshot](./customsd_example.png) of how your service should look when you submit it

1. In your Sonos controller, go to "Add Music Service", then add the service above.

*If you're reinstalling the app then increment the presentation map version, otherwise the previous one will be used. You also need to do this if an update is released with an updated presentation map!*

 See the [TODO list](./TODO.md) for some nice-to-haves.