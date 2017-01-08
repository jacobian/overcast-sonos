# Play [Overcast](https://overcast.fm/) podcasts on your Sonos.

* Fast!
* Remembers last played position
* Syncs play position back to the Overcast service every 30 seconds or when paused/stopped
* Removes episodes from Overcast when completed

Usage:

1. `pip install -r requirements.txt`

1. `OVERCAST_USERNAME=you@there.com OVERCAST_PASSWORD=1234 python overcast-sonos.py`

1. Go to `http://<SONOS_IP>:1400/customsd.htm`, and enter:

    - SID - some unique SID (255 works if you've not done this before
    - Service Name - some name, `overcast` works
    - Endpoint URL and Secure Endpoint URL: `http://<YOUR_IP>:8140/overcast-sonos`
    - Presentation map: version = 1, Uri = `http://<YOUR_IP>:8140/presentation_map`
    - Authentication SOAP header policy: "Anonymous"
    - Check the boxes in the [example screenshot](./customsd_example.png)

 1. In your Sonos controller, go to "Add Music Service", then add the service above.

 See the [TODO list](./TODO.md) for some nice-to-haves.
