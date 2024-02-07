# This file is part of pi-jukebox.
#
# pi-jukebox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pi-jukebox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with pi-jukebox. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) 2015- by Mark Zwart, <mark.zwart@pobox.com>
"""
==================================================================
**mpd_client.py**: controlling and monitoring mpd via python-mpd2.
==================================================================
"""
import logging

from datetime import datetime, timedelta
from dateutil import parser
from mpd.asyncio import MPDClient

logging.basicConfig(
    format='%(levelname)s:\t%(asctime)s - %(module)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DEFAULT_COVER = 'images/default_cover_art.png'


class MPDController(object):
    """ Controls playback and volume
    """

    def __init__(self, host, port = 6600):
        self.mpd_client = MPDClient()
        self._host = host
        self._port = port
        logging.info(f"MPD connection host: {host}, port: {port}")

    async def connect(self) -> bool:
        """ Connects to mpd server.

            :return: Boolean indicating if successfully connected to mpd server.
        """
        if(not self.is_connected):
            try:
                logger.info(f"Connecting to MPD server on {self._host}:{self._port}")
                await self.mpd_client.connect(self._host, self._port)

            except ConnectionError:
                logger.error(f"Failed to connect to MPD server on {self._host}:{self._port}")
                return False
        return True

    @property
    def is_connected(self) -> bool:
        return self.mpd_client.connected

    async def player_control_set(self, play_status):
        """ Controls playback

            :param play_status: Playback action ['play', 'pause', 'stop', 'next', 'previous']
        """
        await self.connect()
        logger.info(f"MPD player control set {play_status}")
        try:
            if play_status == 'play':
                self.mpd_client.play()
            elif play_status == 'pause':
                self.mpd_client.pause(1)
            elif play_status == 'stop':
                self.mpd_client.stop()
            elif play_status == 'next':
                self.mpd_client.next()
            elif play_status == 'previous':
                self.mpd_client.previous()
        except:
            logger.error(f"Could not send {play_status} command to MPD")

    async def seek_current_song_time(self, time_seconds: str):
        """Seeks to the position TIME (in seconds; fractions allowed) within the current song.
           If prefixed by \'+\' or \'-\', then the time is relative to the current playing position.
        """
        await self.connect()
        await self.mpd_client.seekcur(time_seconds)

    async def play_on_queue(self, position: int) -> bool:
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
                await self.mpd_client.play(position)
                logger.info(f"Selected a song at position {position} to start playing.")
                return True
            else:
                logger.error(f"Selected a song at position {position} which is larger than the number of songs in the queue {qty_songs_playlist}")
        else:
            logger.error("Could not retrieve the status of MPD.")
        return False

    async def outputs_get(self) -> list:
        """MPD music stream outputs

        Returns:
            list: A list of dictionaries with stream output info
        """
        logger.info("Retrieving a list of audio outputs.")
        await self.connect()
        outputs = await self.mpd_client.outputs()
        return outputs

    async def output_toggle(self, id_output: int):
        await self.connect()
        logger.info(f"Switch mute on/off for {id_output}")
        test = await self.mpd_client.toggleoutput(id_output)
        outputs = await self.mpd_client.outputs()
        return outputs[id_output]

    # async def __search(self, tag_type):
    #     """ Searches all entries of a certain type.

    #     :param tag_type: ["artist"s, "album"s, song"title"s]
    #     :return: A list with search results.
    #     """
    #     self.list_query_results = self.mpd_client.list(tag_type)
    #     self.list_query_results.sort()
    #     return self.list_query_results

    # async def __search_first_letter(self, tag_type, first_letter):
    #     """ Searches all entries of a certain type matching a first letter

    #     :param tag_type: ["artist"s, "album"s, song"title"s]
    #     :param first_letter: The first letter
    #     :return: A list with search results.
    #     """
    #     temp_results = []
    #     for i in self.list_query_results:
    #         if i[:1].upper() == first_letter.upper():
    #             temp_results.append(i)
    #     self.list_query_results = temp_results
    #     return self.list_query_results

    # async def __search_of_type(self, type_result, type_filter, name_filter):
    #     """ Searching one type depending on another type (very clear description isn't it?)

    #     :param type_result: The type of result-set generated ["artist"s, "album"s, song"title"s]
    #     :param type_filter: The type of filter used ["artist"s, "album"s, song"title"s]
    #     :param name_filter: The name used to filter
    #     :return:
    #     """
    #     if self.searching_artist == "" and self.searching_album == "":
    #         self.list_query_results = self.mpd_client.list(type_result, type_filter, name_filter)
    #     elif self.searching_artist != "" and self.searching_album == "":
    #         self.list_query_results = self.mpd_client.list(type_result, 'artist', self.searching_artist,
    #                                                        type_filter,
    #                                                        name_filter)
    #     elif self.searching_artist == "" and self.searching_album != "":
    #         self.list_query_results = self.mpd_client.list(type_result, 'album', self.searching_album, type_filter,
    #                                                        name_filter)
    #     elif self.searching_artist != "" and self.searching_album != "":
    #         self.list_query_results = self.mpd_client.list(type_result, 'artist', self.searching_artist, 'album',
    #                                                        self.searching_album, type_filter, name_filter)
    #     self.list_query_results.sort()
    #     return self.list_query_results

    async def __get_cover_binary(self, uri: str) -> bytes:
        """Retrieving a file's coverart as a binary stream

        Args:
            uri (str): The file specifier from the MPD library

        Returns:
            bytes: A binary stream representing the file's cover image
        """
        await self.connect()
        try:
            cover = await self.mpd_client.albumart(uri)
            binary = cover['binary']
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
        if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        elif image_data.startswith(b'\xff\xd8'):
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
        return {'image_format': image_format, 'image': image_bytes}

    async def get_album_cover(self, name_artist: str, name_album: str):
        album = await self.get_album(name_artist=name_artist, name_album=name_album)
        if album is None:
            return None
        file = album['files'][0]['file']
        cover_art = await self.get_cover_art(uri=file)
        return cover_art

    async def get_status(self) -> dict:
        """MPD server status

        Returns:
            dict: MPD server status
        """
        await self.connect()
        status = await self.mpd_client.status()
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

    async def get_statistics(self) -> dict:
        """MPD server statistics

        Returns:
            dict: MPD server statistics
        """
        await self.connect()
        dict_stats = await self.mpd_client.stats()
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

    async def get_queue(self) -> list:
        """ Current playlist

        :return: List of dictionaries, with the song information and the information about it's position in the playlist
        """
        await self.connect()
        lst_songs = []
        playlist_pos = 0
        playlist = await self.mpd_client.playlist()

        # Getting complete songs information
        for item in playlist:
            song = await self.mpd_client.find('file', item.replace('file: ', ''))
            song[0]['playlist_pos'] = playlist_pos
            lst_songs = lst_songs + song
            playlist_pos = playlist_pos + 1
        lst_songs = self.__rename_song_dict_keys(lst_songs)
        return lst_songs

    async def current_song(self) -> dict:
        """ Current song in the playlist, regardless whether it is playing, paused or stopped

        :return: A dictionary, with the song information and the information about it's position in the playlist
        """
        await self.connect()
        playing = await self.mpd_client.currentsong()
        playing = self.__rename_song_dict_keys(playing)
        return playing

    async def queue_add(self, type_asset: str, name: str, play: bool=False, replace=False):
        """ Adds a music asset to the current queue

        :param type: The name of the album
        :param filter: The string that should be searched against, the searches are done with partial matching
        :param unknown: I want to play this now by: replacing the playlist, adding it right after
        """
        await self.connect()
        lst_songs = []
        if(not type_asset in ['artist', 'album', 'file']):
            return [{'error': 'incorrect search type'}]

        lst_songs = await self.mpd_client.find(type_asset, name)
        if(lst_songs == None or len(lst_songs) == 0):
            return({'error': type_asset + ' \'' + name + '\' not found.'})

        # Add songs to the current queue
        for song in lst_songs:
            song_added = await self.mpd_client.findadd('file', song['file'])

        return lst_songs

    async def queue_delete(self, start:int, end: int):
        await self.connect()
        await self.mpd_client.delete((start, end+1))
        playlist = await self.get_queue()
        return playlist

    async def queue_move(self, start: int, end: int, to: int):
        await self.connect()
        await self.mpd_client.move((start, end+1), to)
        playlist = await self.get_queue()
        return playlist

    async def queue_add_file(self, file: str, position: int, start_playing: bool, clear: bool=False):
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
            await self.mpd_client.clear()
        await self.mpd_client.addid(file, position)
        if start_playing:
            await self.mpd_client.play(position)
        playlist = await self.get_queue()
        return playlist

    async def queue_clear(self):
        """Clears the current playlist"""
        await self.connect()
        self.mpd_client.clear()

    async def get_artists(self):
        """ All artists in the database

        :return: A list of dictionaries for artists
        """
        await self.connect()
        lst_query_results = await self.mpd_client.list('artist')
        return lst_query_results

    async def get_albums(self):
        """ All albums in the database

        :return: A list of dictionaries for albums with their artists
        """
        await self.connect()
        lst_query_results = await self.mpd_client.list('album', 'group', 'albumartist')
        transformed_list = []

        for entry in lst_query_results:
            albumartist = entry["albumartist"]
            albums = entry["album"]

            if isinstance(albums, list):
                for album in albums:
                    transformed_list.append({"albumartist": albumartist, "album": album})
            else:
                transformed_list.append({"albumartist": albumartist, "album": albums})

        return transformed_list

    async def get_artist_albums(self, name_artist:str) -> list:
        """A list of albums (and their songs) that belong to a specific artists (strict search)

        Args:
            name_artist (str): An exact name for an artist

        Returns:
            list: A list of dictionaries with albums and nested files for each album
        """
        await self.connect()
        lst_query_results = []
        lst_query_results = await self.mpd_client.find('artist', name_artist)
        lst_query_results = self.__type_library(lst_query_results)
        lst_query_results = self.__rename_song_dict_keys(lst_query_results)
        lst_query_results = self.__nest_album(lst_query_results)
        return lst_query_results

    async def get_album(self, name_artist: str, name_album: str):
        await self.connect()
        lst_artist_albums = []
        lst_artist_albums = await self.mpd_client.find('artist', name_artist) #, 'album', name_artist)
        lst_artist_albums = self.__rename_song_dict_keys(lst_artist_albums)
        lst_artist_albums = self.__type_library(lst_artist_albums)
        lst_artist_albums = self.__nest_album(lst_artist_albums)
        try:
            album_dict = [album_dict for album_dict in lst_artist_albums if album_dict['album'] == name_album][0]
        except IndexError as e:
            return None
        return album_dict

    async def search(self, type: str, filter:str):
        """ Searches for artists, albums or songs.

        :param type: The type of music asset that is being searched for (artist, album or song)
        :param filter: The string that should be searched against, the searches are done with partial matching
        :return: A list of dictionaries, with a hierarchy depending on the type of search.
        """
        if(not type in ['artist', 'album', 'song']):
            return [{'error': 'incorrect search type'}]
        if(type == 'song'): # To match MPD internal naming convention
            type = 'title'

        await self.connect()
        list_query_results = await self.mpd_client.search(type, filter)
        list_query_results = self.__rename_song_dict_keys(list_query_results)
        if(len(list_query_results) == 0):
            return({'error': type + ' ' + filter + ' not found.'})

        # Nest files if artists or albums are searched
        if(type == 'artist'):
            list_query_results = self.__nest_artist_album(list_query_results)
        elif(type == 'album'):
            list_query_results = self.__nest_album(list_query_results)
        else:
            list_query_results = list_query_results

        return list_query_results

    async def get_playlists(self)-> list:
        await self.connect()
        lst_playlist = await self.mpd_client.listplaylists()
        return lst_playlist

    async def get_playlist(self, name_playlist: str):
        await self.connect()
        playlist_info = await self.mpd_client.listplaylistinfo(name_playlist)
        playlist_info = self.__rename_song_dict_keys(playlist_info)
        playlist_info = self.__type_library(playlist_info)
        return playlist_info

    async def playlist_add_file(self, name_playlist: str, file: str):
        await self.connect()
        await self.mpd_client.playlistadd(name_playlist, file)

    async def queue_to_playlist(self, name_playlist: str):
        await self.connect()
        await self.mpd_client.save(name_playlist)

    async def playlist_delete_song(self, name_playlist: str, position: int):
        await self.connect()
        playlist = await self.mpd_client.listplaylistinfo(name_playlist)
        qty_songs = len(playlist)
        if position < 0 or position >= qty_songs:
            return False
        else:
            await self.mpd_client.playlistdelete(name_playlist, position)
            return True

    async def playlist_enqueue(self, name_playlist: str, start_playing: bool=False) -> None:
        await self.connect()
        if start_playing:
            status = await self.get_status()
        await self.mpd_client.load(name_playlist)
        if start_playing:
            await self.play_on_queue(position=status['playlistlength'])
        play_queue = await self.get_queue(name_playlist=name_playlist)
        return play_queue

    async def playlist_delete(self, name_playlist: str):
        await self.connect()
        self.mpd_client.rm(name_playlist)

    async def playlist_rename(self, name_playlist: str, name_new: str):
        await self.connect()
        self.mpd_client.rename(name_playlist, name_new)


    def __rename_song_dict_keys(self, data):
        """
        Rename the song key within a list of dictionaries or a single dictionary.

        Parameters:
        - data: List of dictionaries or a single dictionary

        Returns:
        - A new list of dictionaries or a new dictionary with the key renamed from 'title' to 'song'
        """
        old_key_name = 'title'
        new_key_name = 'song'

        if isinstance(data, list):
            # If data is a list of dictionaries
            return [{new_key_name if key == old_key_name else key: value for key, value in item.items()} for item in data]
        elif isinstance(data, dict):
            # If data is a single dictionary
            if old_key_name in data:
                data[new_key_name] = data.pop(old_key_name)
            return data
        else:
            # Handle other types or raise an exception if needed
            raise ValueError("Input data must be a list of dictionaries or a single dictionary.")

    def __type_library(self, data):
        """Converts datatypes to their actual datatypes instead of the strings MPD returns

        Args:
            data (dict or list): A dictionary containing MPD library query results

        Returns:
            dict or list: A (list of) dictionary with converted data types
        """
        if isinstance(data, list):
            # If data is a list of dictionaries
            i = 0
            while i < len(data):
                data[i] = self.__type_library_dict(data[i])
                i += 1
            return data
        elif isinstance(data, dict):
            # If data is a single dictionary
            return self.__type_library_dict(data)
        else:
            # Handle other types or raise an exception if needed
            raise ValueError("Input data must be a list of dictionaries or a single dictionary.")

    def __type_library_dict(self, data) -> dict:
        """Converts datatypes to their actual datatypes instead of the strings MPD returns

        Args:
            data (dict): A dictionary containing MPD library query results

        Returns:
            dict: A dictionary with converted data types
        """
        lst_key_int = ['track', 'disc', 'time']
        lst_key_datetime = ['last-modified']
        lst_float = ['duration']

        for key in lst_key_int:
            if key in data.keys():
                logger.info(f"Converting {key} of {data['file']} to int.")
                try:
                    data[key] = int(data[key])
                except TypeError as e:
                    logger.error(f"Could not convert {key} of {data['file']} to int.")

        for key in lst_key_datetime:
            if key in data.keys():
                logger.info(f"Converting {key} of {data['file']} to datetime.")
                try:
                    data[key] =  parser.parse(data[key])
                except TypeError as e:
                    logger.error(f"Could not convert {key} of {data['file']} to datetime.")
        for key in lst_float:
            if key in data.keys():
                logger.info(f"Converting {key} of {data['file']} to float.")
                try:
                    data[key] = float(data[key])
                except TypeError as e:
                    logger.error(f"Could not convert {key} of {data['file']} to float.")
        return data

    def __nest_artist_album(self, list_dict_files):
        """
        Nesting of files within a hierarchy of artists and their albums

        Parameters:
        - list_dict_files: List of dictionaries that represent music files

        Returns:
        - list of dictionaries that are grouped in a hierarchy by artist and album
        """
        # Initialize a dictionary to store the result
        result_dict = {}

        # Iterate over each dictionary in the list
        for file_data in list_dict_files:
            artist = file_data['artist']
            album = file_data.get('album', '')  # Get 'album' with a default value of an empty string
            file_dict = {key: value for key, value in file_data.items() if key not in ['artist', 'album']}

            # Check if the artist is already in the result_dict
            if artist in result_dict:
                # Check if the album is already in the artist's dictionary
                if album in result_dict[artist]:
                    result_dict[artist][album]['files'].append(file_dict)
                else:
                    result_dict[artist][album] = {'album': album, 'files': [file_dict]}
            else:
                result_dict[artist] = {album: {'album': album, 'files': [file_dict]}}

        # Convert the result_dict to a list of dictionaries
        result_list = [{'artist': artist, 'albums': list(albums.values())} for artist, albums in result_dict.items()]

        return result_list

    def __nest_album(self, list_dict_files):
        """
        Nesting of files within a hierarchy of albums

        Parameters:
        - list_dict_files: List of dictionaries that represent music files

        Returns:
        - list of dictionaries that are grouped in a hierarchy by album
        """
        # Initialize a dictionary to store the result
        result_dict = {}

        # Iterate over each dictionary in the list
        for file_data in list_dict_files:
            album = file_data.get('album', '')  # Get 'album' with a default value of an empty string
            file_dict = {key: value for key, value in file_data.items() }#if key not in ['file']}

            # Check if the album is already in the result_dict
            if album in result_dict:
                result_dict[album]['files'].append(file_dict)
            else:
                result_dict[album] = {'album': album, 'files': [file_dict]}

        # Convert the result_dict to a list of dictionaries
        result_list = list(result_dict.values())

        return result_list