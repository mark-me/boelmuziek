import logging
import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

from lastfm.information_provider import LastFmInfo

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class StatsQuery():
    def __init__(self) -> None:
        self.db_conn = sqlite3.connect("db/lastfm.sqlite")  # ":memory:")

    def __play_years_sql(self, type_asset: str, year: int=None):
        if type_asset == "artists":
            columns = "name_artist, match_artist"
        elif type_asset == "albums":
            columns = "name_artist, match_artist, name_album, match_album"
        elif type_asset == "songs":
            columns = "name_artist, name_song"

        sql_statement = f"""
        SELECT {columns},
            strftime('%Y', dt_played) AS year_played,
            COUNT(*) AS qty_plays,
            MAX(dt_played) AS dt_played_last,
            MIN(dt_played) AS dt_played_first
        FROM song_plays
        """
        if year is not None:
            sql_statement = sql_statement + f" WHERE strftime('%Y', dt_played) = {year} "
        sql_statement = sql_statement + """
        GROUP BY {columns},
            strftime('%Y', dt_played)
        """
        return sql_statement

    def artist_play_years_get(self):
        sql_statement = self.__play_years_sql(type_asset="artists")
        df = pd.read_sql_query(sql_statement, self.db_conn)
        return df.to_dict(orient="records")

    def album_play_years_get(self):
        sql_statement = self.__play_years_sql(type_asset="albums")
        df = pd.read_sql_query(sql_statement, self.db_conn)
        return df.to_dict(orient="records")

    def song_play_years_get(self):
        sql_statement = self.__play_years_sql(type_asset="songs")
        df = pd.read_sql_query(sql_statement, self.db_conn)
        return df.to_dict(orient="records")

    def artist_new_discovery(self):
        sql_statement = """
        SELECT
            cur.name_artist,
            COUNT(*) AS qty_plays,
            MAX(cur.dt_played) AS dt_played_last,
            MIN(cur.dt_played) AS dt_played_first
        FROM song_plays as cur
        WHERE cur.name_artist NOT IN
            ( SELECT name_artist
                FROM song_plays
                WHERE dt_played < DATETIME('now', '-1 year')
                GROUP BY name_artist )
        GROUP BY cur.name_artist
        ORDER BY COUNT(*) DESC
        """
        df = pd.read_sql_query(sql_statement, self.db_conn)
        return df.to_dict(orient="records")

    def artist_rediscover_year(self, year: int) -> dict:
        sql_statement = f"""
        SELECT  name_artist, strftime('%Y', dt_played) AS year
        FROM song_plays
        WHERE CAST(strftime('%Y', dt_played) AS INT) = {year} AND
            name_artist NOT IN
            ( SELECT name_artist
            FROM song_plays
            WHERE CAST(strftime('%Y', dt_played) AS INT) < {year}
            GROUP BY  name_artist)
        GROUP BY  name_artist, strftime('%Y', dt_played)
        """
        df = pd.read_sql_query(sql_statement, self.db_conn)
        return df.to_dict(orient="records")

    def album_new_discovery(self):
        sql_statement = """
        SELECT
            cur.name_artist,
            cur.name_album,
            COUNT(*) AS qty_plays,
            MAX(cur.dt_played) AS dt_played_last,
            MIN(cur.dt_played) AS dt_played_first
        FROM song_plays as cur
        WHERE cur.name_artist || cur.name_album NOT IN
            ( SELECT name_artist || name_album
                FROM song_plays
                WHERE dt_played < DATETIME('now', '-1 year')
                GROUP BY name_artist || name_album )
        GROUP BY cur.name_artist,
                cur.name_album
        ORDER BY COUNT(*) DESC
        """
        df = pd.read_sql_query(sql_statement, self.db_conn)
        return df.to_dict(orient="records")

    def album_rediscover_year(self, year: int) -> dict:
        sql_statement = f"""
        SELECT  name_artist, name_album, strftime('%Y', dt_played) AS year
        FROM song_plays
        WHERE CAST(strftime('%Y', dt_played) AS INT) = {year} AND
            name_artist || name_album NOT IN
            ( SELECT name_artist || name_album
            FROM song_plays
            WHERE CAST(strftime('%Y', dt_played) AS INT) < {year}
            GROUP BY  name_artist || name_album)
        GROUP BY  name_artist, name_album, strftime('%Y', dt_played)
        """
        df = pd.read_sql_query(sql_statement, self.db_conn)
        return df.to_dict(orient="records")

    # def songs_recently_discovered(self):
    #     cur = self.db_conn.cursor()
    #     cur.execute(
    #         """CREATE TABLE IF NOT EXISTS courses
    #                 (Course_ID INTEGER PRIMARY KEY, Course_Name TEXT)"""
    #     )
    #     lst_songs = []
    #     for song in lst_songs:
    #         cur.execute("INSERT INTO courses VALUES (:Course_ID, :Course_Name )", song) #1

    #     self.db_conn.commit()
    #     self.db_conn.close()
