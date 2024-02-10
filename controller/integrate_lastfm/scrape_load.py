from dotenv import dotenv_values

import logging
import os
import sqlite3
import sys

sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

from mpd_client.mpd_client import MPDController
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
mpd_client = MPDController(host=config["HOST_MPD"])

file_db = "config/lastfm.sqlite"
con = sqlite3.connect(file_db)

lastfm = LastFm(host=config["HOST_CONTROLLER"], port=config["PORT_CONTROLLER"])
mpd_client = MPDController(host=config["HOST_MPD"])

lastfm.get_top_assets('albums')