from dotenv import dotenv_values
import pandas as pd

import asyncio
import logging
import os
import sqlite3
import sys

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

# Start main code
lastfm = LastFm(host=config["HOST_CONTROLLER"], port=config["PORT_CONTROLLER"])
library = MPDLibrary(host=config["HOST_MPD"])
con_sqlite = sqlite3.connect(':memory:')

async def main():
    # Get top albums
    lst_albums = lastfm.get_top_assets('albums', limit=100, period="7day")
    df_albums = pd.DataFrame.from_records(lst_albums)
    df_albums.to_sql('albums_lastfm', con_sqlite, if_exists='replace', index=False)
    print("-- Last.fm")
    print(df_albums.head())

    lst_albums = await library.get_albums()
    df_albums = pd.DataFrame.from_records(lst_albums)
    df_albums.to_sql('albums_mpd', con_sqlite, if_exists='replace', index=False)
    print("-- MPD")
    print(df_albums.head())

    sql_statement = "SELECT lfm.name_artist, lfm.name_album, lfm.qty_plays FROM albums_lastfm AS lfm INNER JOIN albums_mpd as mpd ON lfm.name_artist = mpd.albumartist AND lfm.name_album = mpd.album"
    df_albums = pd.read_sql(sql=sql_statement, con=con_sqlite)
    print("-- Join")
    print(df_albums.head())


if __name__ == "__main__":
    asyncio.run(main())