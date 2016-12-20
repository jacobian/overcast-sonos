# Play [Overcast](https://overcast.fm/) podcasts on your Sonos.

**Super-early, rather fragile, barely works.**

Usage:

1. `pip install -r requirements.txt`

1. `OVERCAST_USERNAME=you@there.com OVERCAST_PASSWORD=1234 python overcast-sonos.py`

1. Go to `http://<SONOS_IP>:1400/customsd.htm`, and enter:

    - SID - some unique SID (255 works if you've not done this before
    - Service Name - some name, `overcast` works
    - Endpoint URL and Secure Endpoint URL: `http://<YOUR_IP>:8140/overcast-sonos`
    - Authentication SOAP header policy: "Anonymous"
    - Check the boxes in the example picture

 1. In your Sonos controller, go to "Add Music Service", then add the service above.

 See the [TODO list](./TODO.md) for a list of stuff that doesn't work -- i.e., most of it.
