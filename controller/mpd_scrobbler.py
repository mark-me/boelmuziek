from dotenv import dotenv_values

import asyncio
import logging
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from lastfm import LastFm
from mpd_client import MPDController

logging.basicConfig(
    format='%(levelname)s:\t%(asctime)s - %(module)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def loop_scrobble(lastfm: LastFm, mpd_client: MPDController) -> None:
    """A loop for scrobbling

    Args:
        mpd_host (str): The host of the MPD server
    """
    is_connected = await mpd_client.connect()

    currently_playing :dict = None
    while is_connected:
        async for result in mpd_client.mpd_client.idle(['player']):

            if currently_playing is not None:
                lastfm.scrobble_track(
                    name_artist=currently_playing['artist'],
                    name_song=currently_playing['song'],
                    name_album=currently_playing['album']
                    )

            currently_playing = await mpd_client.current_song()
            if 'song' in currently_playing.keys():
                if 'album' not in currently_playing.keys():
                    currently_playing['album'] = None

                logger.info(f"Sending \'now playing\' {currently_playing['artist']}-{currently_playing['song']} to Last.fm")
                lastfm.now_playing_track(
                    name_artist=currently_playing['artist'],
                    name_song=currently_playing['song'],
                    name_album=currently_playing['album']
                    )
            else:
                currently_playing :dict = None

def main():
    config = {
        **dotenv_values(".env"),  # load shared development variables
        **os.environ,  # override loaded values with environment variables
    }
    lastfm = LastFm(host=config['HOST_CONTROLLER'], port=config['PORT_CONTROLLER'])
    mpd_client = MPDController(host=config['HOST_MPD'])

    is_first_pass = True
    while not lastfm.check_user_data():
        if is_first_pass:
            logger.error("Not authenticated with Last.fm. Use API to login.")
            is_first_pass = False
    logger.info("Successfully logged in Last.fm")
    asyncio.run(loop_scrobble(lastfm=lastfm, mpd_client=mpd_client))

if __name__ == "__main__":
    main()



