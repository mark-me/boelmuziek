from dotenv import dotenv_values

import asyncio
import logging
import os
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from lastfm import LastFm
from mpd_client import MPDController

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# TODO: Wait until there are valid secret keys


class Scrobbler:
    def __init__(self, lastfm: LastFm, mpd_client: MPDController) -> None:
        self.lastfm = lastfm
        self.mpd_client = mpd_client

    async def scrobble(self, song: dict):
        logger.info(f"Scrobble '{song['artist']} - {song['song']}' to Last.fm")
        self.lastfm.scrobble_track(
            name_artist=song['artist'],
            name_song=song['song'],
            name_album=song['album']
            )

    async def send_now_playing(self, song: dict):
        logger.info(
            f"Set '{song['artist']} - {song['song']}' as now playing on Last.fm"
        )
        self.lastfm.now_playing_track(
            name_artist=song['artist'],
            name_song=song['song'],
            name_album=song['album']
            )

    async def get_playing(self):
        playing = await self.mpd_client.current_song()
        if "song" in playing.keys():
            if "album" not in playing.keys():
                playing["album"] = None
        return playing

    async def loop(self) -> None:
        """A loop for scrobbling"""
        is_connected = await self.mpd_client.connect()
        playing: dict = None
        song_scrobbled = playing_sent = {"file": None}
        while is_connected:
            status = await self.mpd_client.get_status()

            if status["state"] == "play":
                playing = await self.get_playing()
                # Now playing
                if status["elapsed"] < status["duration"]:
                    if playing["file"] != playing_sent["file"]:
                        await self.send_now_playing(song=playing)
                        playing_sent = playing
                # Scrobbling
                if status["elapsed"] / status["duration"] > 0.6 or status["elapsed"] > 360:
                    if playing["file"] != song_scrobbled["file"]:
                        await self.scrobble(song=playing)
                        song_scrobbled = playing

            time.sleep(1)

    async def start(self):
        is_first_pass = True
        while not self.lastfm.check_user_data():
            if is_first_pass:
                logger.error("Not authenticated with Last.fm. Use API to login.")
                is_first_pass = False
        logger.info("Successfully logged in Last.fm")
        await self.loop()


def main():
    config = {
        **dotenv_values(".env"),  # load shared development variables
        **os.environ,  # override loaded values with environment variables
    }
    lastfm = LastFm(host=config["HOST_CONTROLLER"], port=config["PORT_CONTROLLER"])
    mpd_client = MPDController(host=config["HOST_MPD"])
    scrobbler = Scrobbler(lastfm=lastfm, mpd_client=mpd_client)
    asyncio.run(scrobbler.start())


if __name__ == "__main__":
    main()
