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


class MPDExtractor:
    def __init__(self) -> None:
        self.library = MPDLibrary(host=config["HOST_MPD"])
        self.con_sqlite = sqlite3.connect(
            "db/lastfm.sqlite", check_same_thread=False
        )

    async def __acquire_mpd_songs(self) -> pd.DataFrame:
        """ Get mpd songs based on last.fm results
        """
        lst_songs = []
        sql_statement = """
        SELECT DISTINCT name_artist, name_song
        FROM songs_lastfm
        """
        df_songs = pd.read_sql(sql=sql_statement, con=self.con_sqlite)
        for _, song in df_songs.iterrows():
            mpd_songs = await self.library.get_song(
                name_artist=song["name_artist"], name_song=song["name_song"]
            )
            if mpd_songs is not None and len(mpd_songs) > 0:
                for mpd_song in mpd_songs:
                    lst_songs = lst_songs + mpd_song["files"]
            return lst_songs

    async def __acquire_mpd_assets(self, type_asset: str) -> None:
        if type_asset == "artists":
            lst_assets = await self.library.get_artists()
        elif type_asset == "albums":
            lst_assets = await self.library.get_albums()
        elif type_asset == "songs":
            lst_assets = await self.__acquire_mpd_songs()
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
        elif type_asset == "songs":
            logger.info(f"Songs dataframe is actually datatype {type(df_assets)}")
            df_assets = df_assets[["file", "artist", "album", "song"]]
        df_assets.to_sql(
            f"{type_asset}_mpd", self.con_sqlite, if_exists="replace", index=False
        )

    async def __acquire_data(self, seconds_interval: int = 1800):
        lst_asset_types = ["artists", "albums", "songs"]

        while True:
            for type_asset in lst_asset_types:
                # Store MPD library
                if type_asset in ["artists", "albums"]: #, "songs"]:
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


def main():
    info = MPDExtractor()
    info.processing_thread()
    while True:
        time.sleep(1800)

if __name__ == "__main__":
    main()
