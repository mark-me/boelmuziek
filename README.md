# BoelMuziek

One music collection, playing everywhere.

A music player that offers diverse navigation options through your music library and allows you to make choices about when to indulge in your favorite tunes. Whether you prefer the intimate experience on the device you're using for navigation or desire to immerse your space in a harmonious ambiance, the player seamlessly extends its capabilities to play music across multiple devices on the local network.

## Components

### Functional
![Functional components](images/components-functional.png)

This schematic looks a bit busy, so let me attempt to explain:

* The **UI** is all the user will see. It allows the user to:
  * search for music,,
  * playing music,
  * switch between streaming music your phone (for example) and the multi-room streamer and
  * control the volume on the client stream, the individual room clients of all room clients simultaneously.
* The UI talks to the **Controller** to:
  * query the music collection,
  * control playback,
  * switch between client and multi-room output and
  * control volume.
* The **Client streamer** can be used to receive playback from the MPD server on the client you are using the app on.
* The **Multi-room streamer** is where all multi-room clients receive their music stream from and can be used to control volume on the **Room receivers**.
* The **Music Library Player** is where the music collection and playback is served

### Technical

This section shows which languages and/or projects are used to implement the functional components.

* The **UI** is implemented needed to be accessible from any kind of device, so it came down to....
* The **Client streamer** is [Icecast](https://icecast.org/), which you can compare to a radio station that is tuned in to whatever you are playing.
* The **Multi-room streamer** solution [Snapcast](https://github.com/badaix/snapcast) is used because it is awesome. I've used this setup for a long time and it is just: AWESOME!
* The **Music Library Player** is [MPD](https://musicpd.org/). Reliable, flexible and around since the dawn of civilization (2003).
* The **Controller** is where several back-end services  are called so the UI developer doesn't need to worry about handling each of the component's quirks and hopefully get some kind of unifief interface. Since the author is uses Python, [FastAPI](https://fastapi.tiangolo.com/) seemed a viable solution.


![Technical components](images/components-technical.png)



## Set-up

The total stack can be deployed by using [Docker Compose](https://docs.docker.com/compose/install/) and the docker-compose.yml file found in the repo's root directory. Before firing up the docker compose you need to:

* Create stack specific directories that need to be made up front which should be readable and writable by all containers, you can use/adjust and execute the file ```init.sh``` to create them.
* change the ```DIR_``` variables in the ```.env``` file to reflect your system. The ```DIR_MUSIC``` variable should point to your music collection.

After firing up docker compose, you have a stack which consists of the following components:

* [MPD](https://musicpd.org/) is a server side music player which also allows querying it's music library.
* [ympd](https://ympd.org/) is a temporary MPD web client, included here to quickly review the stack's functionality. Once the stack is deployed you can find it at http://localhost:8080
* [Icecast](https://icecast.org/) is used to stream music to the client. You can listen to the playback stream at http://localhost:8000/mpd
* [Snapcast server](https://github.com/badaix/snapcast) is used to stream the music over the LAN to be received by all subscribed clients using Snapcast's client. Access the volume of all clients at http://localhost:1780/.
* [Controller](http://localhost:5000/) - Start of a self built [FastAPI](https://fastapi.tiangolo.com/) interface to MPD. Visiting http://localhost:5000/ gets you to the meat of how to communicate with it from your UI. If you are developing your UI you do all API requests to ```localhost```, if you put it in production change the host to ```controller```.

How each components is created can be found within it's own subdirectory:

```bash
.
├── controller  'Developing playback commands, states and library querying'
├── icecast     'Stream music to client'
├── mpd         'The music library player'
├── snapserver  'Snapcast server that serves audio for multi-room purposes'
├── ui          'Developing UI'
└── ympd        'Contains a temporary UI that will de replaced by the developing ui'
```
