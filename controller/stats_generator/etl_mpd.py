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
        SELECT DISTINCT albumartist, album
        FROM albums_mpd
        """
        df_albums = pd.read_sql(sql=sql_statement, con=self.con_sqlite)
        for _, album in df_albums.iterrows():
            mpd_album = await self.library.get_album(
                name_artist=album["albumartist"], name_album=album["album"]
            )
            mpd_songs = mpd_album["files"]
            if mpd_songs is not None and len(mpd_songs) > 0:
                for mpd_song in mpd_songs:
                    song = await self.library.get_file_info(file=mpd_song["file"])
                    lst_songs = lst_songs + song
            return lst_songs

    async def __etl_artists(self) -> None:
        lst_artists = await self.library.get_artists()
        df_artists = pd.DataFrame.from_records(lst_artists)
        df_artists["artist_match"] = (
            df_artists["artist"]
            .str.lower()
            .str.replace('"', "")
            .str.replace("'", "")
        )
        # Sort DataFrame by the length of 'artist' column in descending order
        df_artists = df_artists.sort_values(
            by="artist", key=lambda x: x.str.len(), ascending=False
        )
        # Drop duplicates in 'name_artist' column, keeping the first occurrence
        df_artists = df_artists.drop_duplicates(subset="artist_match", keep="first")
        df_artists.to_sql(
            f"artists_mpd", self.con_sqlite, if_exists="replace", index=False
        )
    async def __etl_albums(self) -> pd.DataFrame:
        lst_albums = await self.library.get_albums()
        df_albums = pd.DataFrame.from_records(lst_albums)
        df_albums["artist_match"] = (
            df_albums["albumartist"]
            .str.lower()
            .str.replace('"', "")
            .str.replace("'", "")
        )
        df_albums["album_match"] = (
            df_albums["album"].str.lower().str.replace('"', "").str.replace("'", "")
        )
        df_albums.to_sql(
            f"albums_mpd", self.con_sqlite, if_exists="replace", index=False
        )
        return df_albums

    async def __etl_songs(dir_album: str) -> None:
        pass

    async def __etl_loop(self, seconds_interval: int = 1800):
        lst_asset_types = ["artists", "albums", "songs"]

        while True:
            await self.__etl_artists()
            await self.__etl_albums()
            # for _, row in df_albums.iterrows():
            #     album = await self.library.get_album(name_artist=row["albumartist"], name_album=row['album'])
            #     pass
            #for type_asset in lst_asset_types:
                # Store MPD library
            #     if type_asset in ["songs"]: # "artists", "albums"]: #
            #         await self.__acquire_mpd_assets(type_asset=type_asset)
            time.sleep(seconds_interval)

    def etl_schedule(self, seconds_interval: int = 1800):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.__etl_loop(seconds_interval))
        loop.close()

    def start_etl_thread(self, seconds_interval: int = 1800):
        daemon = Thread(
            target=self.etl_schedule,
            args=(seconds_interval,),
            daemon=True,
            name="Lastfm Process",
        )
        daemon.start()


def main():
    info = MPDExtractor()
    info.start_etl_thread()
    while True:
        time.sleep(1800)

if __name__ == "__main__":
    main()
