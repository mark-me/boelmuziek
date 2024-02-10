import logging

from mpd_client import helper
from mpd_client.mpd_connector import MPDConnection

logging.basicConfig(
    format='%(levelname)s:\t%(asctime)s - %(module)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MPDPlaylist(MPDConnection):
    def __init__(self, host, port=6600):
        super(MPDPlaylist, self).__init__(host=host, port=port)

    async def get_playlists(self)-> list:
        await self.connect()
        lst_playlist = await self.mpd.listplaylists()
        return lst_playlist

    async def get_playlist(self, name_playlist: str):
        await self.connect()
        playlist_info = await self.mpd.listplaylistinfo(name_playlist)
        playlist_info = helper.rename_song_dict_keys(playlist_info)
        playlist_info = helper.type_library(playlist_info)
        return playlist_info

    async def playlist_add_file(self, name_playlist: str, file: str):
        await self.connect()
        await self.mpd.playlistadd(name_playlist, file)

    async def queue_to_playlist(self, name_playlist: str):
        await self.connect()
        await self.mpd.save(name_playlist)

    async def playlist_delete_song(self, name_playlist: str, position: int):
        await self.connect()
        playlist = await self.mpd.listplaylistinfo(name_playlist)
        qty_songs = len(playlist)
        if position < 0 or position >= qty_songs:
            return False
        else:
            await self.mpd.playlistdelete(name_playlist, position)
            return True

    async def playlist_enqueue(self, name_playlist: str, start_playing: bool=False) -> None:
        await self.connect()
        if start_playing:
            status = await self.mpd.status()
            qty_items_playlist = int(status['playlistlength'])
        await self.mpd.load(name_playlist)
        if start_playing:
            await self.play_on_queue(position=qty_items_playlist)
        play_queue = await self.get_queue(name_playlist=name_playlist)
        return play_queue

    async def playlist_delete(self, name_playlist: str):
        await self.connect()
        self.mpd.rm(name_playlist)

    async def playlist_rename(self, name_playlist: str, name_new: str):
        await self.connect()
        self.mpd.rename(name_playlist, name_new)
