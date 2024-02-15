import asyncio
import logging
import os
import time

from dotenv import dotenv_values

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from lastfm.lastfm import LastFm
from mpd_client.mpd_server import MPDController
from mpd_client.mpd_queue import MPDQueue

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# TODO: Wait until there are valid secret keys


class StopWatch:
    """A stopwatch class
    """
    def __init__(self) -> None:
        self.time_started: float = None
        self.time_paused: float = 0
        self.is_paused = False

    def start(self) -> None:
        """Starts an internal timer by recording the current time"
        """
        self.time_started = time.time()

    def pause(self) -> None:
        """Pauses the stopwatch

        Raises:
            ValueError: Stopwatch was never started
            ValueError: Stopwatch is not paused
        """
        if self.time_started is None:
            raise ValueError("Timer not started")
        if self.is_paused:
            raise ValueError("Timer is already paused")
        self.time_paused = time.time()
        self.is_paused = True

    def resume(self) -> None:
        """Resuming the Stopwatch after pause

        Raises:
            ValueError: Stopwatch was never started
            ValueError: Stopwatch is not paused
        """
        if self.time_started is None:
            self.start()
        if not self.is_paused:
            self.start()
        time_pause = time.time() - self.time_paused
        self.time_started = self.time_started + time_pause
        self.is_paused = False

    def get_seconds(self) -> float:
        """Returns the number of seconds elapsed since the start time, less any pauses

        Returns:
            float: Number of seconds, with decimals for fractions
        """
        if self.time_started is None:
            return 0
        if self.is_paused:
            return self.time_paused - self.time_started
        else:
            return time.time() - self.time_started


class Scrobbler:
    """Listens to MPD to scrobble plays to Last.fm
    """
    def __init__(
        self,
        host_controller: str,
        port_controller: int,
        host_mpd: str,
        port_mpd: int = 6600,
    ) -> None:
        self.lastfm = LastFm(host=host_controller, port=port_controller)
        self.mpd = MPDController(host=host_mpd, port=port_mpd)
        self.queue = MPDQueue(host=host_mpd, port=port_mpd)
        self.stopwatch = StopWatch()

    async def scrobble(self, song: dict):
        """Scrobble a song to lastfm

        Args:
            song (dict): Song information necessary to post scrobble
        """
        logger.info(f"Scrobble '{song['artist']} - {song['song']}' to Last.fm")
        self.lastfm.scrobble_track(
            name_artist=song["artist"], name_song=song["song"], name_album=song["album"]
        )

    async def send_now_playing(self, song: dict):
        logger.info(
            f"Set '{song['artist']} - {song['song']}' as now playing on Last.fm"
        )
        self.lastfm.now_playing_track(
            name_artist=song["artist"], name_song=song["song"], name_album=song["album"]
        )

    async def get_playing(self) -> dict:
        """Get information on the song that is currently playing

        Returns:
            dict: Currently playing song information
        """
        playing = await self.queue.current_song()
        if "song" in playing.keys():
            if "album" not in playing.keys():
                playing["album"] = None
        return playing

    async def __sync_mpd_state_to_stopwatch(self):
        await self.mpd.connect()
        status = await self.mpd.get_status()
        if status["state"] == 'play':
            self.stopwatch.start()
        elif status["state"] == "pause":
            self.stopwatch.start()
            self.stopwatch.pause()

    async def loop(self) -> None:
        """A loop for scrobbling"""
        is_connected = await self.mpd.connect()
        await self.__sync_mpd_state_to_stopwatch()
        playing: dict = None
        prev_playing: dict=None

        while is_connected:
            async for result in self.mpd.mpd.idle(["player"]):
                status = await self.mpd.get_status()
                player_state = status["state"]

                if player_state == "stop":
                    logger.info("Stopped playback")
                    playing = await self.get_playing()
                    sec_elapsed = self.stopwatch.get_seconds()
                    perc_played = sec_elapsed / float(playing["duration"])
                    if perc_played > 0.5 or sec_elapsed > 360:
                        logger.info("Scrobbling song")
                        await self.scrobble(song=playing)
                elif player_state == "play":
                    if playing != prev_playing:
                        logger.info("Next track started playing")
                        # Use previous track stats for scrobbling
                        sec_elapsed = self.stopwatch.get_seconds()
                        perc_played = sec_elapsed / float(playing["duration"])
                        if perc_played > 0.5 or sec_elapsed > 360:
                            logger.info("Scrobbling song")
                            await self.scrobble(song=playing)
                        # Set now playing
                        playing = await self.get_playing()
                        self.lastfm.now_playing_track(
                            name_artist= playing['artist'],
                            name_song=playing['song']
                        )
                        self.stopwatch.start()
                    else:
                        logger.info("Resumed after pause")
                        self.stopwatch.resume()
                elif player_state == "pause":
                    logger.info("Paused playback")
                    self.stopwatch.pause()
                    prev_playing = playing

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

    scrobbler = Scrobbler(
        host_controller=config["HOST_CONTROLLER"],
        port_controller=config["PORT_CONTROLLER"],
        host_mpd=config["HOST_MPD"],
    )
    asyncio.run(scrobbler.start())


if __name__ == "__main__":
    main()
