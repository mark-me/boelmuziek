import datetime
import json
import logging
import sqlite3

from dateutil import parser
from lastfmxpy import (
    methods,
    params,
)
import pandas as pd

from lastfm_client import LastFmClient

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class LastFmInfo(LastFmClient):
    def __init__(self) -> None:
        super(LastFmInfo, self).__init__()
        self.db_conn = sqlite3.connect("db/lastfm.sqlite")  # ":memory:")

    def get_artist_bio(self, name_artist: str) -> str:
        response: str = self._client.post(
            method=methods.Artist.GET_INFO,
            params=params.ArtistGetInfo(artist=name_artist),
            additional_params=dict(format="json"),
        )
        artist = json.loads(response)["artist"]
        return artist["bio"]["content"]

    def get_top_assets(
        self, type_asset: str, period: str = "overall", page: int = 1
    ) -> dict:
        lst_results = []

        if type_asset == "artists":
            response: str = self._client.post(
                method=methods.User.GET_TOP_ARTISTS,
                params=params.UserGetTopArtists(
                    user=self._username, period=period, page=page
                ),
                additional_params=dict(format="json"),
            )
            top_items = json.loads(response)
            top_items = top_items["topartists"]["artist"]
        elif type_asset == "albums":
            response: str = self._client.post(
                method=methods.User.GET_TOP_ALBUMS,
                params=params.UserGetTopAlbums(
                    user=self._username, period=period, page=page
                ),
                additional_params=dict(format="json"),
            )
            top_items = json.loads(response)
            top_items = top_items["topalbums"]["album"]
        elif type_asset == "songs":
            response: str = self._client.post(
                method=methods.User.GET_TOP_TRACKS,
                params=params.UserGetTopTracks(
                    user=self._username, period=period, page=page
                ),
                additional_params=dict(format="json"),
            )
            top_items = json.loads(response)
            top_items = top_items["toptracks"]["track"]
        if len(top_items) == 0:
            return [
                {
                    "status_code": 404,
                    "details": f"No more {type_asset} for the period {period} results on page {page}",
                }
            ]
        for top_item in top_items:
            if type_asset == "artists":
                dict_top_item = {
                    "name_artist": top_item["name"],
                    "qty_plays": int(top_item["playcount"]),
                }
            elif type_asset == "albums":
                dict_top_item = {
                    "name_artist": top_item["artist"]["name"],
                    "name_album": top_item["name"],
                    "qty_plays": int(top_item["playcount"]),
                }
            elif type_asset == "songs":
                dict_top_item = {
                    "name_artist": top_item["artist"]["name"],
                    "name_song": top_item["name"],
                    "qty_plays": int(top_item["playcount"]),
                }
            lst_results.append(dict_top_item)
        return lst_results

    def get_loved_tracks(self, page: int = 1) -> list:
        logger.info(f"Get {self._username}'s loved tracks")
        result = self._client.post(
            method=methods.User.GET_LOVED_TRACKS,
            params=params.UserGetLovedTracks(
                user=self._username, page=page, api_key=self._api_key
            ),
            additional_params=dict(format="json"),
        )
        lst_tracks = json.loads(result)["lovedtracks"]["track"]
        lst_loved_tracks = []
        for track in lst_tracks:
            lst_loved_tracks.append(
                {
                    "datetime": parser.parse(track["date"]["#text"]),
                    "timestamp": int(track["date"]["uts"]),
                    "name_song": track["name"],
                    "name_artist": track["artist"]["name"],
                }
            )
        return lst_loved_tracks

    def get_recent_songs(self, time_to: str, time_from: str = 0, page: int = 1):
        lst_songs = []
        response: str = self._client.post(
            method=methods.User.GET_RECENT_TRACKS,
            params=params.UserGetRecentTracks(
                user=self._username,
                page=page,
                extended=True,
                to=time_to,
                from_=time_from,
                limit=1000,
            ),
            additional_params=dict(format="json"),
        )
        recent_songs = json.loads(response)
        recent_songs = recent_songs["recenttracks"]["track"]
        for recent_song in recent_songs:
            lst_songs.append(
                {
                    "name_artist": recent_song["artist"]["name"],
                    "name_song": recent_song["name"],
                    "name_album": recent_song["album"]["#text"],
                    "dt_played": parser.parse(recent_song["date"]["#text"]),
                }
            )
        return lst_songs

    def extract_recent_songs(self):
        recent_songs: list = None
        now = datetime.datetime.utcnow
        page = 1
        while recent_songs is None or len(recent_songs) > 0:
            recent_songs = self.get_recent_songs(time_to=now, page=page)
            df = pd.DataFrame(recent_songs)
            df.to_sql(
                name="song_played", con=self.db_conn, if_exists="append", index=False
            )
            page = page + 1

    def __song_play_create_table(self):
        sql_statement = """
        CREATE TABLE IF NOT EXISTS song_plays (
            name_artist     TEXT,
            name_album      TEXT,
            name_song       TEXT,
            dt_played       TIMESTAMP,
            match_artist    TEXT,
            match_album     TEXT,
            match_song      TEXT
        )
        """
        cur = self.db_conn.cursor()
        cur.execute(sql_statement)
        self.db_conn.commit()

    def __song_play_stage(self, recent_songs: dict) -> str:
        table_stage = "song_plays_stage"
        # Create data-frame and transform data
        df = pd.DataFrame(recent_songs)
        cols_dest = ["match_artist", "match_album", "match_song"]
        cols_replace = ["name_artist", "name_album", "name_song"]
        df[cols_dest] = (
            df[cols_replace]
            .apply(lambda x: x.str.lower())
            .apply(lambda x: x.str.replace("'", ""))
            .apply(lambda x: x.str.replace('"', ""))
        )
        # Write stage table
        df.to_sql(
            name=table_stage, con=self.db_conn, if_exists="replace", index=False
        )
        return table_stage

    def __song_play_load(self, table_stage: str) -> None:
        table_dest = "song_plays"
        self.__song_play_create_table()
        sql_add_to_dest = f"""
        INSERT INTO {table_dest}
        SELECT
            tmp.name_artist,
            tmp.name_album,
            tmp.name_song,
            tmp.dt_played,
            tmp.match_artist,
            tmp.match_album,
            tmp.match_song
        FROM {table_stage} as tmp
        LEFT JOIN {table_dest} as dest
            ON dest.name_artist = tmp.name_artist AND
                dest.name_album = tmp.name_album AND
                dest.name_song = tmp.name_song AND
                dest.dt_played = tmp.dt_played
        WHERE dest.dt_played IS NULL
        """
        cur = self.db_conn.cursor()
        cur = cur.execute(sql_add_to_dest)
        qty_added = cur.rowcount
        self.db_conn.commit()
        return qty_added

    def song_play_process(self):
        now = datetime.datetime.utcnow
        page = 1
        while True:
            # Extract
            recent_songs = self.get_recent_songs(time_to=now, page=page)
            if len(recent_songs) == 0:
                break
            # Stage
            table_stage = self.__song_play_stage(recent_songs=recent_songs)
            # Load
            qty_added = self.__song_play_load(table_stage=table_stage)
            page = page + 1

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


def main():
    info = LastFmInfo()
    dict_result = info.song_play_process()
    print(dict_result)


if __name__ == "__main__":
    main()
