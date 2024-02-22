from dotenv import dotenv_values
import pandas as pd

import asyncio
import logging
import os
import sqlite3
import sys
import time
from threading import Thread

sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

from mpd_client.mpd_library import MPDLibrary
from lastfm.lastfm import LastFm

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


class LastFmMusicLibrarySyncer:
    def __init__(self, mpd_library: MPDLibrary, lastfm: LastFm) -> None:
        self.lastfm = lastfm
        self.library = mpd_library
        self.con_sqlite = sqlite3.connect(
            "lastfm.sqlite", check_same_thread=False
        )  # ":memory:"
        self.loved_songs = []
        self.top_artists = []

    def __acquire_top_lastfm(self, type_asset: str, period: str, limit: int):
        lst_assets = self.lastfm.get_top_assets(
            type_asset=type_asset, limit=limit, period=period
        )
        df_assets = pd.DataFrame.from_records(lst_assets)
        df_assets["period"] = period
        cols_replace = []
        if type_asset == "artists":
            cols_replace = ["name_artist"]
        elif type_asset == "albums":
            cols_replace = ["name_artist", "name_album"]
        elif type_asset == "songs":
            cols_replace = ["name_artist", "name_song"]
        df_assets[cols_replace] = (
            df_assets[cols_replace]
            .apply(lambda x: x.str.lower())
            .apply(lambda x: x.str.replace("'", ""))
            .apply(lambda x: x.str.replace('"', ""))
        )
        return df_assets

    async def __acquire_mpd_assets(self, type_asset: str) -> None:
        if type_asset == "artists":
            lst_assets = await self.library.get_artists()
        elif type_asset == "albums":
            lst_assets = await self.library.get_albums()
        else:
            return None
        df_assets = pd.DataFrame.from_records(lst_assets)
        if type_asset == "artists":
            df_assets["artist_match"] = (
                df_assets["artist"]
                .str.lower()
                .str.replace('"', "")
                .str.replace("'", "")
            )
            # Sort DataFrame by the length of 'artist' column in descending order
            df_assets = df_assets.sort_values(
                by="artist", key=lambda x: x.str.len(), ascending=False
            )
            # Drop duplicates in 'name_artist' column, keeping the first occurrence
            df_assets = df_assets.drop_duplicates(subset="artist_match", keep="first")
        elif type_asset == "albums":
            df_assets["artist_match"] = (
                df_assets["albumartist"]
                .str.lower()
                .str.replace('"', "")
                .str.replace("'", "")
            )
            df_assets["album_match"] = (
                df_assets["album"].str.lower().str.replace('"', "").str.replace("'", "")
            )
        df_assets.to_sql(
            f"{type_asset}_mpd", self.con_sqlite, if_exists="replace", index=False
        )

    async def __acquire_data(self, seconds_interval: int = 1800):
        lst_periods = ["overall", "7day", "1month", "3month", "6month", "12month"]
        lst_asset_types = ["artists", "albums", "songs"]

        while True:
            for type_asset in lst_asset_types:
                lst_dfs = []
                for period in lst_periods:
                    logger.info(f"Getting top played {type_asset} for period {period}")
                    df = self.__acquire_top_lastfm(
                            type_asset=type_asset, period=period, limit=1000
                        )
                    lst_dfs.append(df)
                df = pd.concat(lst_dfs)
                # Store Last.fm results
                df.to_sql(
                    f"{type_asset}_lastfm", self.con_sqlite, if_exists="replace", index=False
                )
                # Store MPD library
                if type_asset in ["artists", "albums"]:
                    await self.__acquire_mpd_assets(type_asset=type_asset)
            time.sleep(seconds_interval)

    def start_processing(self, seconds_interval: int = 1800):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.__acquire_data(seconds_interval))
        loop.close()

    def processing_thread(self, seconds_interval: int = 1800):
        daemon = Thread(
            target=self.start_processing,
            args=(seconds_interval,),
            daemon=True,
            name="Lastfm Process",
        )
        daemon.start()

    # async def acquire_top_artists(self, period: str, limit: int = 1000):
    #     self.__acquire_top_lastfm(type_asset="artists", period=period, limit=limit)
    #     await self.__acquire_mpd_assets(type_asset="artists")

    #     sql_statement = """SELECT
    #                             lfm.name_artist,
    #                             lfm.qty_plays
    #                         FROM artists_lastfm AS lfm
    #                         INNER JOIN artists_mpd as mpd
    #                             ON lfm.name_artist = mpd.artist"""
    #     df_artists = pd.read_sql(sql=sql_statement, con=self.con_sqlite)
    #     return df_artists

    # async def get_top_albums(self, period: str, limit: int = 1000) -> dict:
    #     self.__acquire_top_lastfm(type_asset="albums", period=period, limit=limit)
    #     await self.__acquire_mpd_assets(type_asset="albums")

    #     sql_statement = """SELECT
    #                             lfm.name_artist,
    #                             lfm.name_album,
    #                             lfm.qty_plays
    #                         FROM albums_lastfm AS lfm
    #                         INNER JOIN albums_mpd as mpd
    #                             ON lfm.name_artist = mpd.albumartist AND
    #                                 lfm.name_album = mpd.album"""
    #     df_albums = pd.read_sql(sql=sql_statement, con=self.con_sqlite)
    #     return df_albums

    async def __get_mpd_songs(self, lst_source) -> list:
        lst_songs = []
        for song_lastfm in lst_source:
            mpd_song = await self.library.get_song(
                name_song=song_lastfm["name_song"],
                name_artist=song_lastfm["name_artist"],
            )
            if len(mpd_song) > 0:
                mpd_song = mpd_song[0]
                if "qty_plays" in song_lastfm.keys():
                    mpd_song["qty_plays"] = song_lastfm["qty_plays"]
                lst_songs.append(mpd_song)
        return lst_songs

    async def __get_mpd_song(self, lastfm_song: dict) -> list:
        mpd_song = await self.library.get_song(
            name_song=lastfm_song["name_song"],
            name_artist=lastfm_song["name_artist"],
        )
        if len(mpd_song) > 0:
            mpd_song = mpd_song[0]
            if "qty_plays" in mpd_song.keys():
                mpd_song["qty_plays"] = mpd_song["qty_plays"]
        return mpd_song

    async def get_top_songs(self, period: str, limit: int = 1000) -> dict:
        lst_lastfm = self.lastfm.get_top_assets(
            type_asset="songs", limit=limit, period=period
        )
        lst_songs = await self.__get_mpd_songs(lst_source=lst_lastfm)
        return lst_songs

    async def get_loved_songs(self, limit: int = 1000):
        lst_lastfm = self.lastfm.get_loved_tracks(limit=limit)
        lst_songs = await self.__get_mpd_songs(lst_source=lst_lastfm)
        return lst_songs

    async def get_loved(self, limit: int = 50, page=1):
        for track in self.lastfm.loved_tracks():
            lst_lastfm = self.lastfm.loved_tracks(limit=limit, page=page)
        lst_songs = await self.__get_mpd_songs(lst_source=lst_lastfm)
        return lst_songs


async def main():
    lastfm = LastFm(host=config["HOST_CONTROLLER"], port=config["PORT_CONTROLLER"])
    library = MPDLibrary(host=config["HOST_MPD"])

    matched = LastFmMusicLibrarySyncer(mpd_library=library, lastfm=lastfm)
    matched.processing_thread()
    while True:
        time.sleep(1800)


if __name__ == "__main__":
    asyncio.run(main())
