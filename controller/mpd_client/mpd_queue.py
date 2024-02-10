import logging

from mpd_client import helper
from mpd_client.mpd_connector import MPDConnection

logging.basicConfig(
    format='%(levelname)s:\t%(asctime)s - %(module)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MPDQueue(MPDConnection):
    def __init__(self, host, port=6600):
        super(MPDQueue, self).__init__(host=host, port=port)

    async def get_queue(self) -> list:
        """ Current playlist

        :return: List of dictionaries, with the song information and the information about it's position in the playlist
        """
        await self.connect()
        lst_songs = []
        playlist_pos = 0
        playlist = await self.mpd.playlist()

        # Getting complete songs information
        for item in playlist:
            song = await self.mpd.find('file', item.replace('file: ', ''))
            song[0]['playlist_pos'] = playlist_pos
            lst_songs = lst_songs + song
            playlist_pos = playlist_pos + 1
        lst_songs = helper.rename_song_dict_keys(lst_songs)
        lst_songs = helper.type_library(lst_songs)
        return lst_songs

    async def play(self, position: int) -> bool:
        """Begins playing the queue at song at _position

        Args:
            position (int): The position of a song in the queue

        Returns:
            bool: Success of play selection
        """
        await self.connect()
        status = await self.get_status()
        if status is not None:
            qty_songs_playlist = status['playlistlength']
            if qty_songs_playlist > position:
                await self.mpd.play(position)
                logger.info(f"Selected a song at position {position} to start playing.")
                return True
            else:
                logger.error(f"Selected a song at position {position} which is larger than the number of songs in the queue {qty_songs_playlist}")
        else:
            logger.error("Could not retrieve the status of MPD.")
        return False

    async def current_song(self) -> dict:
        """ Current song in the playlist, regardless whether it is playing, paused or stopped

        :return: A dictionary, with the song information and the information about it's position in the playlist
        """
        await self.connect()
        playing = await self.mpd.currentsong()
        playing = helper.rename_song_dict_keys(playing)
        return playing

    async def add(self, type_asset: str, name: str, play: bool=False, replace=False):
        """ Adds a music asset to the current queue

        :param type: The name of the album
        :param filter: The string that should be searched against, the searches are done with partial matching
        :param unknown: I want to play this now by: replacing the playlist, adding it right after
        """
        await self.connect()
        lst_songs = []
        if(type_asset not in ['artist', 'album', 'file']):
            return [{'error': 'incorrect search type'}]

        lst_songs = await self.mpd.find(type_asset, name)
        if(lst_songs is None or len(lst_songs) == 0):
            return({'error': type_asset + ' \'' + name + '\' not found.'})

        # Add songs to the current queue
        for song in lst_songs:
            await self.mpd.findadd('file', song['file'])

        return lst_songs

    async def delete_items(self, start:int, end: int):
        await self.connect()
        await self.mpd.delete((start, end+1))
        playlist = await self.get_queue()
        return playlist

    async def move_items(self, start: int, end: int, to: int):
        await self.connect()
        await self.mpd.move((start, end+1), to)
        playlist = await self.get_queue()
        return playlist

    async def add_file(self, file: str, position: int, start_playing: bool, clear: bool=False):
        """Adds a file to the queue

        Args:
            file (str): A file to be added
            position (int): The position at which the file is added to the playlist
            start_playing (bool): Start playing the file immediately
            clear (bool, optional): Clear the playlist before adding the file. Defaults to False.

        Returns:
            _type_: _description_
        """
        await self.connect()
        if clear:
            position = 0
            await self.mpd.clear()
        await self.mpd.addid(file, position)
        if start_playing:
            await self.mpd.play(position)
        playlist = await self.get_queue()
        return playlist

    async def clear(self):
        """Clears the current playlist"""
        await self.connect()
        self.mpd.clear()