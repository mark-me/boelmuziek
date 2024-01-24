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
import pandas as pd
from mpd.asyncio import MPDClient
from collections import deque

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


class MPDNowPlaying(object):
    """ Song information
    """
    def __init__(self, mpd_client):
        self.__mpd_client = mpd_client
        self.playing_type = ''
        self.__now_playing = None
        self.title = ""  # Current playing song name
        self.artist = ""  # Current playing artist
        self.album = ""  # Album the currently playing song is on
        self.file = ""  # File with path relative to MPD music directory
        self.__time_current_sec = 0  # Current playing song time (seconds)
        self.time_current = ""  # Current playing song time (string format)
        self.__time_total_sec = 0  # Current playing song duration (seconds)
        self.time_total = ""  # Current playing song duration (string format)
        self.time_percentage = 0  # Current playing song time as a percentage of the song duration
        self.music_directory = ""

    def now_playing_set(self, now_playing=None):
        if now_playing is not None:
            try:
                self.file = now_playing['file']
            except KeyError:
                logging.error("Could not read filename of nowplaying")
                return False
            if self.file[:7] == "http://":
                self.playing_type = 'radio'
            else:
                self.playing_type = 'file'

            if 'title' in now_playing:
                self.title = now_playing['title']  # Song title of current song
            else:
                self.title = os.path.splitext(os.path.basename(now_playing['file']))[0]
            if self.playing_type == 'file':
                if 'artist' in now_playing:
                    self.artist = now_playing['artist']  # Artist of current song
                else:
                    self.artist = "Unknown"
                if 'album' in now_playing:
                    self.album = now_playing['album']  # Album the current song is on
                else:
                    self.album = "Unknown"
                current_total = self.str_to_float(now_playing['time'])
                self.__time_total_sec = current_total
                self.time_total = self.make_time_string(current_total)  # Total time current
            elif self.playing_type == 'radio':
                if 'name' in now_playing:
                    self.album = now_playing['name']  # The radio station name
                else:
                    self.album = "Unknown"
                self.artist = ""
        elif now_playing is None:  # Changed to no current song
            self.__now_playing = None
            self.title = ""
            self.artist = ""
            self.album = ""
            self.file = ""
            self.time_percentage = 0
            self.__time_total_sec = 0
            self.time_total = self.make_time_string(0)  # Total time current
        return True

    async def get_cover_binary(self, uri):
        try:
            logging.info("Start first try to get cover art from %s", uri)
            cover = await self.__mpd_client.albumart(uri)
            binary = cover['binary']
            logging.info("End first try to get cover art")
        except:
            logging.warning("Could not retrieve album cover of %s", uri)
            binary = None
        return binary

    async def get_cover_art(self):
        blob_cover = await self.get_cover_binary(self.file)
        if blob_cover is None:
            file_cover_art = "default_cover_art.png"
        else:
            with open('covert_art.img', 'wb') as img:
                img.write(blob_cover)  # write artwork to new image
            file_cover_art = "covert_art.img"
        return file_cover_art

    def current_time_set(self, seconds):
        if self.__time_current_sec != seconds:  # Playing time current
            self.__time_current_sec = seconds
            self.time_current = self.make_time_string(seconds)
            if self.playing_type != 'radio':
                self.time_percentage = int(self.__time_current_sec / self.__time_total_sec * 100)
            else:
                self.time_percentage = 0
            return True
        else:
            return False

    def make_time_string(self, seconds):
        minutes = int(seconds / 60)
        seconds_left = int(round(seconds - (minutes * 60), 0))
        time_string = str(minutes) + ':'
        seconds_string = ''
        if seconds_left < 10:
            seconds_string = '0' + str(seconds_left)
        else:
            seconds_string = str(seconds_left)
        time_string += seconds_string
        return time_string

    def str_to_float(self, s):
        try:
            return float(s)
        except ValueError:
            return float(0)


class MPDController(object):
    """ Controls playback and volume
    """

    def __init__(self, host, port = 6600):
        self.mpd_client = MPDClient()
        self.host = host
        self.port = port
        self.update_interval = 1000  # Interval between mpc status update calls (milliseconds)
        self.volume = 0  # Playback volume
        self.now_playing = MPDNowPlaying(self.mpd_client)  # Dictionary containing currently playing song info
        self.events = deque([])  # Queue of mpd events

        self.__now_playing_changed = True
        self.__player_control = ''  # Indicates whether mpd is playing, pausing or has stopped playing music
        self.__muted = False  # Indicates whether muted
        self.__last_update_time = 0  # For checking last update time (milliseconds)
        self.__status = None  # mpc's current status output

         # Database search results
        self.searching_artist = ""  # Search path user goes through
        self.searching_album = ""
        self.list_albums = []
        self.list_artists = []
        self.list_songs = []
        self.list_query_results = []

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
        self.now_playing.now_playing_set(current_song)
        return True

    @property
    def is_connected(self) -> bool:
        return self.mpd_client.connected

    def disconnect(self):
        """ Closes the connection to the mpd server. """
        logging.info("Closing down MPD connection")
        self.mpd_client.close()
        self.mpd_client.disconnect()

    async def __parse_mpc_status(self):
        """ Parses the mpd status and fills mpd event queue

            :return: Boolean indicating if the status was changed
        """
        logging.info("Trying to get mpd status")
        self.mpd_client.ping() # Wake up MPD
        # Song information
        now_playing_new = await self.mpd_client.currentsong()
        if self.now_playing != now_playing_new and len(now_playing_new) > 0:  # Changed to a new song
            self.__now_playing_changed = True
            if self.now_playing is None or self.now_playing.file != now_playing_new['file']:
                self.events.append('playing_file')
            self.__radio_mode = self.now_playing.playing_type == 'radio'
            if self.now_playing.album == '' or self.now_playing.album != now_playing_new['album']:
                logging.info("Album change event added")
                self.events.append('album_change')
            self.now_playing.now_playing_set(now_playing_new)
        # Player status
        status = await self.mpd_client.status()
        if self.__status == status:
            return False
        self.__status = status
        if self.__player_control != status['state']:
            self.__player_control = status['state']
            self.events.append('player_control')
        if self.__player_control != 'stop':
            if self.now_playing.current_time_set(self.str_to_float(status['elapsed'])):
                self.events.append('time_elapsed')
        return True

    def str_to_float(self, s):
        try:
            return float(s)
        except ValueError:
            return float(0)

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

    def current_song_changed(self):
        if self.__now_playing_changed:
            self.__now_playing_changed = False
            return True
        else:
            return False

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

    async def __search_partial(self, tag_type, part):
        """ Searches all entries of a certain type partially matching search string.

        :param tag_type: ["artist"s, "album"s, song"title"s]
        :param part: Search string.
        :return: A list with search results.
        """
        self.list_query_results = []
        all_results = self.mpd_client.list(tag_type)
        async for result in all_results:
            if result[tag_type].upper().find(part.upper()) > -1:
                self.list_query_results.append(result)
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

    async def artists_get(self, part: str=None, only_start: bool=True) -> list:
        """ Retrieves all artist names or matching by first letter(s) or partial search string.

        :param part: Search string
        :param only_start: Only search as first letter(s).
        :return: A list of matching artist names.
        """
        self.searching_artist = ""
        self.searching_album = ""
        if part is None:
            if len(self.list_artists) == 0:
                self.list_artists = await self.__search('artist')
            return self.list_artists
        elif only_start:
            self.list_query_results = await self.__search_first_letter('artist', part)
        else:
            self.list_query_results = await self.__search_partial('artist', part)
        return self.list_query_results

    async def albums_get(self, part: str=None, only_start: bool=True) -> list:
        """ Retrieves all album titles or matching by first letter(s) or partial search string.

        :param part: Search string.
        :param only_start: Only search as first letter(s).
        :return: A list of matching album titles.
        """
        self.searching_artist = ""
        self.searching_album = ""
        if part is None:
            if len(self.list_albums) == 0:
                self.list_albums = await self.__search('album')
            return self.list_albums
        elif only_start:
            self.list_query_results = await self.__search_first_letter('album', part)
        else:
            self.list_query_results = await self.__search_partial('album', part)
        return self.list_query_results

    async def songs_get(self, part: str=None, only_start: bool=True) -> list:
        """ Retrieves all song titles or matching by first letter(s) or partial search string

        :param part: Search string
        :param only_start: Only search as first letter(s)
        :return: A list of matching song titles
        """
        self.searching_artist = ""
        self.searching_album = ""
        if part is None:
            if len(self.list_songs) == 0:
                self.list_songs = await self.__search('title')
            return self.list_songs
        elif only_start:
            self.list_query_results = await self.__search_first_letter('title', part)
        else:
            self.list_query_results = await self.__search_partial('title', part)
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

    async def search(self, type: str, filter:str):
        list_query_results = await self.mpd_client.search(type, filter)
        df_results = pd.DataFrame(list_query_results)
        if(type == 'artist'):
            self.list_query_results = df_results \
                .fillna('') \
                .groupby(['artist']) \
                .apply(lambda x: x.drop(['artist',], axis=1)) \
                .groupby(['album']) \
                .apply(lambda x: x.drop(['album',], axis=1).to_dict(orient='records'))
        elif(type == 'album'):
            df_results = df_results.loc[:, df_results.columns.intersection(['albumartist', 'album'])].drop_duplicates()

        #df_results = df_results.fillna('')
        #self.list_query_results = df_results.to_dict('records')
        return self.list_query_results