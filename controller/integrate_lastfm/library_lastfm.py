from dotenv import dotenv_values
import pandas as pd

import logging
import os
import sqlite3
import sys

sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class LibraryStats:
    def __init__(self) -> None:
        self.con_sqlite = sqlite3.connect(
            "lastfm.sqlite", check_same_thread=False
        )  # ":memory:"

    def get_artist_stats(self, period: str="overall") -> dict:
        sql_statement = """SELECT
                                lfm.name_artist,
                                lfm.qty_plays
                            FROM artists_lastfm AS lfm
                            INNER JOIN artists_mpd as mpd
                                ON lfm.name_artist = mpd.artist"""
        sql_statement = sql_statement + f" WHERE period = {period}"
        df_artists = pd.read_sql(sql=sql_statement, con=self.con_sqlite)
        dict_artists = df_artists.to_dict(orient="records")
        return dict_artists

    def get_album_stats(self, period: str="overall") -> dict:
        sql_statement = """SELECT
                                lfm.name_artist,
                                lfm.name_album,
                                lfm.qty_plays
                            FROM albums_lastfm AS lfm
                            INNER JOIN albums_mpd as mpd
                                ON lfm.name_artist = mpd.albumartist AND
                                    lfm.name_album = mpd.album"""
        sql_statement = sql_statement + f" WHERE period = {period}"
        df_albums = pd.read_sql(sql=sql_statement, con=self.con_sqlite)
        dict_albums = df_albums.to_dict(orient="records")
        return dict_albums

    def get_song_stats(self, period: str="overall") -> dict:
        sql_statement = """
        SELECT
            a.name_song,
            a.name_artist,
            a.period,
            a.qty_plays,
            b.album,
            b.file
        FROM songs_lastfm AS a
        LEFT JOIN songs_mpd as b
            ON  b.artist = a.name_artist AND
                b.song = a.name_song
        """
        sql_statement = sql_statement + f" WHERE period = {period}"
        df_songs = pd.read_sql_query(sql=sql_statement, con=self.con_sqlite)
        dict_songs = df_songs.to_dict(orient="records")
        return dict_songs

