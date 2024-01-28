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

import os
import time
from datetime import datetime
from dateutil import parser
from mpd.asyncio import MPDClient
from collections import deque
from collections import defaultdict

MPD_TYPE_ARTIST = 'artist'
MPD_TYPE_ALBUM = 'album'
MPD_TYPE_SONGS = 'title'

DEFAULT_COVER = 'images/default_cover_art.png'
TEMP_PLAYLIST_NAME = '_pi-jukebox_temp'


def retry(func, ex_type=Exception, limit=0, wait_ms=100, wait_increase_ratio=2, logger=None):
    """
    Retry a function invocation until no exception occurs
    :param func: function to invoke
    :param ex_type: retry only if exception is subclass of this type
    :param limit: maximum number of invocation attempts
    :param wait_ms: initial wait time after each attempt in milliseconds.
    :param wait_increase_ratio: increase wait period by multiplying this value after each attempt.
    :param logger: if not None, retry attempts will be logged to this logging.logger
    :return: result of first successful invocation
    :raises: last invocation exception if attempts exhausted or exception is not an instance of ex_type
    """
    attempt = 1
    while True:
        try:
            return func()
        except Exception as ex:
            if not isinstance(ex, ex_type):
                raise ex
            if 0 < limit <= attempt:
                if logger:
                    logger.warning("no more attempts")
                raise ex

            if logger:
                logger.error("failed execution attempt #%d", attempt, exc_info=ex)

            attempt += 1
            if logger:
                logger.info("waiting %d ms before attempt #%d", wait_ms, attempt)
            time.sleep(wait_ms / 1000)
            wait_ms *= wait_increase_ratio


class MPDController(object):
    """ Controls playback and volume
    """

    def __init__(self, host, port = 6600):
        self.mpd_client = MPDClient()
        self.host = host
        self.port = port

    async def connect(self):
        """ Connects to mpd server.
            :return: Boolean indicating if successfully connected to mpd server.
        """
        try:
            await self.mpd_client.connect(self.host, self.port)
        except ConnectionError:
            logging.error("Failed to connect to MPD server: host: ", self.host, " port: ", self.port)
            return False
        current_song = await self.mpd_client.currentsong()
        return True

    @property
    def is_connected(self) -> bool:
        return self.mpd_client.connected

    def disconnect(self):
        """ Closes the connection to the mpd server. """
        logging.info("Closing down MPD connection")
        self.mpd_client.close()
        self.mpd_client.disconnect()

    async def status_get(self):
        """ Updates mpc data, returns True when status data is updated. Wait at
            least 'update_interval' milliseconds before updating mpc status data.

            :return: Returns boolean whether updated or not.
        """
        time_elapsed = round(time.time()*1000) - self.__last_update_time
        if round(time.time()*1000) > self.update_interval > time_elapsed:
            return False
        self.__last_update_time = round(time.time()*1000)  # Reset update
        return await self.__parse_mpc_status()  # Parse mpc status output

    def player_control_set(self, play_status):
        """ Controls playback

            :param play_status: Playback action ['play', 'pause', 'stop', 'next', 'previous']
        """
        logging.info("MPD player control %s", play_status)
        try:
            if play_status == 'play':
                if self.__player_control == 'pause':
                    self.mpd_client.play()
                else:
                    self.mpd_client.pause(0)
            elif play_status == 'pause':
                self.mpd_client.pause(1)
            elif play_status == 'stop':
                self.mpd_client.stop()
            elif play_status == 'next':
                self.mpd_client.next()
            elif play_status == 'previous':
                self.mpd_client.previous()
        except:
            logging.error("Could not send %s command to MPD", play_status)

    async def outputs_get(self) -> list:
        outputs = await self.mpd_client.outputs()
        return outputs

    async def output_toggle(self, id_output: int):
        test = await self.mpd_client.toggleoutput(id_output)
        outputs = await self.mpd_client.outputs()
        return outputs[id_output]

    async def player_control_get(self):
        """ :return: Current playback mode. """
        await self.status_get()
        return self.__player_control

    async def __search(self, tag_type):
        """ Searches all entries of a certain type.

        :param tag_type: ["artist"s, "album"s, song"title"s]
        :return: A list with search results.
        """
        self.list_query_results = self.mpd_client.list(tag_type)
        self.list_query_results.sort()
        return self.list_query_results

    async def __search_first_letter(self, tag_type, first_letter):
        """ Searches all entries of a certain type matching a first letter

        :param tag_type: ["artist"s, "album"s, song"title"s]
        :param first_letter: The first letter
        :return: A list with search results.
        """
        temp_results = []
        for i in self.list_query_results:
            if i[:1].upper() == first_letter.upper():
                temp_results.append(i)
        self.list_query_results = temp_results
        return self.list_query_results

    async def __search_of_type(self, type_result, type_filter, name_filter):
        """ Searching one type depending on another type (very clear description isn't it?)

        :param type_result: The type of result-set generated ["artist"s, "album"s, song"title"s]
        :param type_filter: The type of filter used ["artist"s, "album"s, song"title"s]
        :param name_filter: The name used to filter
        :return:
        """
        if self.searching_artist == "" and self.searching_album == "":
            self.list_query_results = self.mpd_client.list(type_result, type_filter, name_filter)
        elif self.searching_artist != "" and self.searching_album == "":
            self.list_query_results = self.mpd_client.list(type_result, 'artist', self.searching_artist,
                                                           type_filter,
                                                           name_filter)
        elif self.searching_artist == "" and self.searching_album != "":
            self.list_query_results = self.mpd_client.list(type_result, 'album', self.searching_album, type_filter,
                                                           name_filter)
        elif self.searching_artist != "" and self.searching_album != "":
            self.list_query_results = self.mpd_client.list(type_result, 'artist', self.searching_artist, 'album',
                                                           self.searching_album, type_filter, name_filter)
        self.list_query_results.sort()
        return self.list_query_results

    def artist_albums_get(self, artist_name):
        """ Retrieves artist's albums.

        :param artist_name: The name of the artist to retrieve the albums of.
        :return: A list of album titles.
        """
        self.searching_artist = artist_name
        return self.__search_of_type('album', 'artist', artist_name)

    def artist_songs_get(self, artist_name):
        """ Retrieves artist's songs.

        :param artist_name: The name of the artist to retrieve the songs of.
        :return: A list of song titles
        """
        self.searching_artist = artist_name
        return self.__search_of_type('title', 'artist', artist_name)

    def album_songs_get(self, album_name):
        """ Retrieves all song titles of an album.

        :param album_name: The name of the album
        :return: A list of song titles
        """
        self.searching_album = album_name
        return self.__search_of_type('title', 'album', album_name)

    async def get_cover_binary(self, uri):
        try:
            cover = await self.mpd_client.albumart(uri)
            binary = cover['binary']
        except:
            logging.warning("Could not retrieve album cover of %s", uri)
            binary = None
        return binary

    async def get_status(self):
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
        return status

    async def playlist(self):
        """ Current playlist

        :return: List of dictionaries, with the song information and the information about it's position in the playlist
        """
        lst_songs = []
        playlist_pos = 1
        playlist = await self.mpd_client.playlist()

        # Getting complete songs information
        for item in playlist:
            song = await self.mpd_client.find('file', item.replace('file: ', ''))
            song[0]['playlist_pos'] = playlist_pos
            lst_songs = lst_songs + song
            playlist_pos = playlist_pos + 1
        lst_songs = self.__rename_song_dict_keys(lst_songs)
        return lst_songs

    async def current_song(self):
        """ Current song in the playlist, regardless whether it is playing, paused or stopped

        :return: A dictionary, with the song information and the information about it's position in the playlist
        """
        playing = await self.mpd_client.currentsong()
        playing = self.__rename_song_dict_keys(playing)
        return playing

    async def playlist_add(self, type_asset: str, name: str, play: bool=False, replace=False):
        """ Adds a music asset to the current playlist

        :param type: The name of the album
        :param filter: The string that should be searched against, the searches are done with partial matching
        :param unknown: I want to play this now by: replacing the playlist, adding it right after
        """
        #TODO: Add option for replacing playlist (and play)
        lst_songs = []
        if(not type_asset in ['artist', 'album', 'file']):
            return [{'error': 'incorrect search type'}]

        lst_songs = await self.mpd_client.find(type_asset, name)
        if(lst_songs == None or len(lst_songs) == 0):
            return({'error': type_asset + ' \'' + name + '\' not found.'})

        # Add songs to the current playlist
        for song in lst_songs:
            song_added = await self.mpd_client.findadd('file', song['file'])

        return lst_songs

    async def playlist_add_file(self, file: str, position: int, start_playing: bool):
        await self.mpd_client.addid(file, position)
        if start_playing:
            await self.mpd_client.play(position)
        playlist = await self.playlist()
        return playlist

    async def playlist_clear(self):
        """Clears the current playlist"""
        self.mpd_client.clear()

    async def get_artists(self):
        """ All artists in the database

        :return: A list of dictionaries for artists
        """
        lst_query_results = await self.mpd_client.list('artist')
        return lst_query_results

    async def get_albums(self):
        """ All albums in the database

        :return: A list of dictionaries for albums with their artists
        """
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
        lst_query_results = []
        lst_query_results = await self.mpd_client.find('artist', name_artist)
        lst_query_results = self.__type_library(lst_query_results)
        lst_query_results = self.__rename_song_dict_keys(lst_query_results)
        lst_query_results = self.__nest_album(lst_query_results)
        return lst_query_results

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

        list_query_results = await self.mpd_client.search(type, filter)
        list_query_results = self.__rename_song_dict_keys(list_query_results)
        if(len(list_query_results) == 0):
            return({'error': type + ' ' + filter + ' not found.'})

        if(type == 'artist'):
            self.list_query_results = self.__nest_artist_album(list_query_results)
        elif(type == 'album'):
            self.list_query_results = self.__nest_album(list_query_results)
        else:
            self.list_query_results = list_query_results

        return self.list_query_results

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

    def __type_library_dict(self, data):
        lst_key_int = ['track', 'disc', 'time']
        lst_key_datetime = ['last-modified']
        #lst_date = ['date'] #, 'originaldate']
        lst_float = ['duration']

        for key in lst_key_int:
            if key in data.keys():
                data[key] = int(data[key])
        for key in lst_key_datetime:
            if key in data.keys():
                data[key] =  parser.parse(data[key])
        # for key in lst_date:
        #     if key in data.keys():
        #         data[key] = datetime.strptime(data[key], '%Y-%m-%d').date()
        for key in lst_float:
            if key in data.keys():
                data[key] = float(data[key])
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