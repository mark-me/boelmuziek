from datetime import datetime, timedelta
import logging

from mpd.asyncio import MPDClient

from mpd_client.mpd_connector import MPDConnection

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DEFAULT_COVER = "images/default_cover_art.png"


class MPDController(MPDConnection):
    """Controls playback and volume"""

    def __init__(self, host, port=6600):
        super(MPDController, self).__init__(host=host, port=port)

    async def get_status(self) -> dict:
        """MPD server status

        Returns:
            dict: MPD server status
        """
        await self.connect()
        status = await self.mpd.status()
        lst_int = ['volume', 'playlist', 'playlistlength', 'mixrampdb',
                   'song', 'songid', 'nextsong', 'nextsongid']
        for item in lst_int:
            if item in status.keys():
                status[item] = int(status[item])
        lst_bool = ['repeat', 'random', 'single', 'consume']
        for item in lst_bool:
            if item in status.keys():
                status[item] = bool(int(status[item]))
        lst_float = ['elapsed', 'duration']
        for item in lst_float:
            if item in status.keys():
                status[item] = float(status[item])
        return status

    async def player_control_set(self, play_status):
        """Controls playback

        :param play_status: Playback action ['play', 'pause', 'stop', 'next', 'previous']
        """
        await self.connect()
        logger.info(f"MPD player control set {play_status}")
        try:
            if play_status == "play":
                self.mpd.play()
            elif play_status == "pause":
                self.mpd.pause(1)
            elif play_status == "stop":
                self.mpd.stop()
            elif play_status == "next":
                self.mpd.next()
            elif play_status == "previous":
                self.mpd.previous()
        except MPDClient.CommandError:
            logger.error(f"Could not send {play_status} command to MPD")

    async def seek_current_song_time(self, time_seconds: str):
        """Seeks to the position TIME (in seconds; fractions allowed) within the current song.
        If prefixed by \'+\' or \'-\', then the time is relative to the current playing position.
        """
        await self.connect()
        await self.mpd.seekcur(time_seconds)

    async def get_outputs(self) -> list:
        """MPD music stream outputs

        Returns:
            list: A list of dictionaries with stream output info
        """
        logger.info("Retrieving a list of audio outputs.")
        await self.connect()
        outputs = await self.mpd.outputs()
        for output in outputs:
            output['outputenabled'] = (True if output['outputenabled'] == "1" else False)
        return outputs

    async def output_toggle(self, id_output: int):
        await self.connect()
        logger.info(f"Switch mute on/off for {id_output}")
        await self.mpd.toggleoutput(id_output)
        outputs = await self.get_outputs()
        return outputs[id_output]

    async def get_statistics(self) -> dict:
        """MPD server statistics

        Returns:
            dict: MPD server statistics
        """
        await self.connect()
        dict_stats = await self.mpd.stats()
        lst_int = ['artists', 'albums', 'songs']
        for item in lst_int:
            if item in dict_stats.keys():
                dict_stats[item] = int(dict_stats[item])
        lst_time_elapsed = ['db_playtime', 'uptime', 'playtime']
        for item in lst_time_elapsed:
            if item in dict_stats.keys():
                dict_stats[item] = str(timedelta(seconds=int(dict_stats[item])))
        if 'db_update' in dict_stats.keys():
            dict_stats['db_update'] = datetime.fromtimestamp(int(dict_stats['db_update']))
        return(dict_stats)

    async def update_db(self) -> int:
        """Update the MPD music library to reflect changes to the music files.

        Returns:
            int: The update run triggered since the MPD server start
        """
        await self.connect()
        update = await self.mpd.update()
        return update
