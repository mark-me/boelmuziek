import asyncio
import logging
import os
import time

from dotenv import dotenv_values

from lastfm.player_listening import LastFmListening
from mpd_client.mpd_server import MPDController
from mpd_client.mpd_queue import MPDQueue

os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# TODO: Wait until there are valid secret keys


class StopWatch:
    """A stopwatch class"""

    def __init__(self) -> None:
        self._time_started: float = None
        self._time_paused: float = 0
        self._is_paused = False

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def start(self) -> None:
        """Starts an internal timer by recording the current time" """
        self._time_started = time.time()

    def pause(self) -> None:
        """Pauses the stopwatch

        Raises:
            ValueError: Stopwatch was never started
            ValueError: Stopwatch is not paused
        """
        if self._time_started is None:
            raise ValueError("Timer not started")
        if self._is_paused:
            raise ValueError("Timer is already paused")
        self._time_paused = time.time()
        self._is_paused = True

    def resume(self) -> None:
        """Resuming the Stopwatch after pause

        Raises:
            ValueError: Stopwatch was never started
            ValueError: Stopwatch is not paused
        """
        if self._time_started is None:
            self.start()
        if not self._is_paused:
            self.start()
        time_pause = time.time() - self._time_paused
        self._time_started = self._time_started + time_pause
        self._is_paused = False

    def get_seconds(self) -> float:
        """Returns the number of seconds elapsed since the start time, less any pauses

        Returns:
            float: Number of seconds, with decimals for fractions
        """
        if self._time_started is None:
            return 0
        if self._is_paused:
            return self._time_paused - self._time_started
        else:
            return time.time() - self._time_started


class Scrobbler:
    """Listens to MPD to scrobble plays to Last.fm"""

    def __init__(
        self,
        host_mpd: str,
        port_mpd: int = 6600,
    ) -> None:
        self.lastfm = LastFmListening()
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
        if status["state"] == "play":
            self.stopwatch.start()
        elif status["state"] == "pause":
            self.stopwatch.start()
            self.stopwatch.pause()

    async def __gather_play_status(self, prev_playing_track):
        status = await self.mpd.get_status()
        control_state = status["state"]

        # Handling empty now playing track
        playing = await self.get_playing()
        if playing == {}:
            playing = None
        else:
            playing["duration"] = float(playing["duration"])

        # Handling empty previous playing track
        if prev_playing_track == {} or prev_playing_track is None:
            prev_playing_track = None
        else:
            prev_playing_track["duration"] = float(prev_playing_track["duration"])

        # Combine information to inform Last.fm action
        dict_indicators = {
            "control_state": control_state,
            "control_status": status,
            "playing": playing,
            "playing_previous": prev_playing_track,
            "stopwatch_paused": self.stopwatch.is_paused,
            "stopwatch_seconds": self.stopwatch.get_seconds(),
        }
        return dict_indicators

    async def __post_to_lastfm(self, dict_indicators: dict) -> None:
        playing_track = dict_indicators["playing"]
        prev_playing_track = dict_indicators["playing_previous"]
        control_state = dict_indicators["control_state"]

        if control_state == "pause":
            pass
        elif control_state == "play":
            # Set to 'now playing'
            await self.send_now_playing(song=playing_track)
            if (
                prev_playing_track is not None
                and prev_playing_track["file"] != playing_track["file"]
            ):
                # Scrobble
                perc_played = (
                    dict_indicators["stopwatch_seconds"]
                    / prev_playing_track["duration"]
                )
                if perc_played > 0.5 or dict_indicators["stopwatch_seconds"] > 360:
                    await self.scrobble(song=prev_playing_track)
        elif control_state == "stop" and playing_track is not None:
            perc_played = (
                dict_indicators["stopwatch_seconds"] / playing_track["duration"]
            )
            if perc_played > 0.5 or dict_indicators["stopwatch_seconds"] > 360:
                await self.scrobble(song=playing_track)

    async def loop(self) -> None:
        """A loop for scrobbling"""
        is_connected = await self.mpd.connect()
        await self.__sync_mpd_state_to_stopwatch()
        status = await self.mpd.get_status()
        control_state = prev_control_state = status["state"]
        prev_playing_track: dict = None

        dict_indicators = await self.__gather_play_status(
            prev_playing_track=prev_playing_track
        )
        await self.__post_to_lastfm(dict_indicators=dict_indicators)

        while is_connected:
            async for result in self.mpd.mpd.idle(["player"]):
                status = await self.mpd.get_status()
                control_state = status["state"]

                dict_indicators = await self.__gather_play_status(
                    prev_playing_track=prev_playing_track
                )
                await self.__post_to_lastfm(dict_indicators=dict_indicators)

                # Stopwatch
                if control_state == "play":
                    if prev_control_state == "pause":
                        self.stopwatch.resume()
                    elif prev_control_state == "play" or prev_control_state == "stop":
                        self.stopwatch.start()
                elif control_state == "pause":
                    self.stopwatch.pause()

                prev_playing_track = await self.get_playing()
                prev_control_state = control_state

    async def start(self):
        is_first_pass = True
        while not self.lastfm.check_user_data():
            if is_first_pass:
                logger.error("Not authenticated with Last.fm. Use API to login.")
                is_first_pass = False
            time.sleep(3)
        logger.info("Successfully logged in Last.fm")
        await self.loop()


def main():
    config = {
        **dotenv_values(".env"),  # load shared development variables
        **os.environ,  # override loaded values with environment variables
    }

    scrobbler = Scrobbler(
        host_mpd=config["HOST_MPD"],
    )
    asyncio.run(scrobbler.start())


if __name__ == "__main__":
    main()
