import logging
import os
import random as rnd

from mpd_client import helper
from mpd_client.mpd_connector import MPDConnection

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class MPDLibrary(MPDConnection):
    def __init__(self, host, port=6600):
        super(MPDLibrary, self).__init__(host=host, port=port)

    async def __get_cover_binary(self, uri: str) -> bytes:
        """Retrieving a file's coverart as a binary stream

        Args:
            uri (str): The file specifier from the MPD library

        Returns:
            bytes: A binary stream representing the file's cover image
        """
        await self.connect()
        try:
            cover = await self.mpd.albumart(uri)
            binary = cover["binary"]
            logger.info(f"Retrieved album art for {uri}")
        except:
            logger.warning("Could not retrieve album cover of %s", uri)
            binary = None
        return binary

    def __determine_image_format(self, image_data: bytes) -> str:
        """Function to determine image format (PNG or JPG) based on magic bytes

        Args:
            image_data (bytes): A byte stream that represents an image

        Raises:
            ValueError: When encountering a different format than either PNG or JPG

        Returns:
            str: A MIME type string
        """
        if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif image_data.startswith(b"\xff\xd8"):
            return "image/jpeg"
        else:
            raise ValueError("Unsupported image format")

    async def get_cover_art(self, uri: str) -> dict:
        """Retrieve covert art of a file

        Args:
            uri (str): The file specifier from the MPD library

        Returns:
            dict: The MIME type of the art and the image in the form of a byte stream
        """
        await self.connect()
        image_bytes: bytes = await self.__get_cover_binary(uri=uri)
        image_format = self.__determine_image_format(image_bytes)
        return {"image_format": image_format, "image": image_bytes}

    async def get_album_cover(self, name_artist: str, name_album: str):
        await self.connect()
        album = await self.get_artist_albums(
            name_artist=name_artist, name_album=name_album
        )
        if album is None:
            return None
        file = album["files"][0]["file"]
        cover_art = await self.get_cover_art(uri=file)
        return cover_art

    async def get_artists(self):
        """All artists in the database

        :return: A list of dictionaries for artists
        """
        await self.connect()
        try:
            lst_query_results = await self.mpd.list("artist")
        except ConnectionError:
            lst_query_results = None
        return lst_query_results

    async def get_artists_random(self, qty_artists :int=15):
        lst_artists = await self.get_artists()
        lst_results = rnd.sample(lst_artists, qty_artists)
        return lst_results

    async def get_albums(self):
        """All albums in the database

        :return: A list of dictionaries for albums with their artists
        """
        await self.connect()
        try:
            lst_query_results = await self.mpd.list("album", "group", "albumartist")
        except ConnectionError:
            return None
        transformed_list = []

        for entry in lst_query_results:
            albumartist = entry["albumartist"]
            albums = entry["album"]

            if isinstance(albums, list):
                for album in albums:
                    transformed_list.append(
                        {"albumartist": albumartist, "album": album}
                    )
            else:
                transformed_list.append({"albumartist": albumartist, "album": albums})

        return transformed_list

    async def get_albums_random(self, qty_albums :int=15):
        lst_albums = await self.get_albums()
        lst_results = rnd.sample(lst_albums, qty_albums)
        return lst_results

    async def get_album(self, name_artist: str, name_album: str) -> list:
        lst_artist_albums = await self.get_artist_albums(name_artist=name_artist)
        lst_results = [album for album in lst_artist_albums if album['album'] == name_album]
        if len(lst_results) > 0:
            return lst_results[0]
        else:
            return None

    async def get_artist_albums(self, name_artist: str) -> list:
        """A list of albums (and their songs) that belong to a specific artists (strict search)

        Args:
            name_artist (str): An exact name for an artist

        Returns:
            list: A list of dictionaries with albums and nested files for each album
        """
        await self.connect()
        lst_query_results = []
        lst_query_results = await self.mpd.find("artist", name_artist)
        lst_query_results = helper.type_library(lst_query_results)
        lst_query_results = helper.rename_song_dict_keys(lst_query_results)
        lst_query_results = helper.nest_album(lst_query_results)
        return lst_query_results

    async def get_song(self, name_song: str, name_artist: str=None, is_cover: bool=False) -> list:
        await self.connect()
        lst_songs = []
        lst_songs = await self.mpd.search("title", name_song)
        # Improve dict interpretability
        lst_songs = helper.rename_song_dict_keys(lst_songs)
        lst_songs = helper.type_library(lst_songs)
        if name_artist is not None:
            if is_cover:
                lst_songs = [song for song in lst_songs if song['artist'] != name_artist]
            else:
                lst_songs = [song for song in lst_songs if song['artist'] == name_artist]
            lst_songs = helper.nest_album(lst_songs)
        else:
            lst_songs = helper.nest_artist_album(lst_songs)
        return lst_songs

    async def get_file_info(self, file: str) -> dict:
        dir = os.path.dirname(file)
        song = await self.mpd.listallinfo(dir)
        return song

    async def search(self, type: str, filter: str, starts_with: bool = False):
        """Searches for artists, albums or songs.

        :param type: The type of music asset that is being searched for (artist, album or song)
        :param filter: The string that should be searched against, the searches are done with partial matching
        :return: A list of dictionaries, with a hierarchy depending on the type of search.
        """
        if len(filter) < 3:
            return {
                "Error": "Provide at least 3 characters in the search string to start searching"
            }
        if type not in ["artist", "album", "song"]:
            return [{"error": "incorrect search type"}]
        if type == "song":  # To match MPD internal naming convention
            type = "title"

        await self.connect()
        list_query_results = await self.mpd.search(type, filter)
        if len(list_query_results) == 0:
            return {"error": type + " " + filter + " not found."}

        if starts_with:
            list_query_results = [
                item
                for item in list_query_results
                if item[type][: (len(filter))].upper() == filter.upper()
            ]

        # Improve dict interpretability
        list_query_results = helper.rename_song_dict_keys(list_query_results)
        list_query_results = helper.type_library(list_query_results)

        # Nest files if artists or albums are searched
        if type == "artist":
            list_query_results = helper.nest_artist_album(list_query_results)
        elif type == "album":
            list_query_results = helper.nest_album(list_query_results)
        else:
            list_query_results = list_query_results

        return list_query_results
