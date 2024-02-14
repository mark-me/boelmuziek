import pylast
from dotenv import dotenv_values
from dateutil import parser

import logging
import os
import time

from utils import SecretsYAML

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


class LastFm:
    def __init__(self, host: str, port: int) -> None:
        self._secrets = {"session_key": "", "username": ""}
        self._user_secrets_file = SecretsYAML(
            file_path="config/secrets.yml",
            app="lastfm",
            expected_keys=set(self._secrets.keys()),
        )
        self._api_key = "2e031e7b2ab98c1bce14436016185a4d"
        self._api_secret = "fcce22fac65bcdcfcc249841f4ffed8b"

        self._network = pylast.LastFMNetwork(
            api_key=self._api_key, api_secret=self._api_secret
        )
        self._session_key_gen = pylast.SessionKeyGenerator(self._network)

        self.check_user_data()

    def check_user_data(self):
        result = self._user_secrets_file.read_secrets()
        if result is not None:
            logger.info(
                "Found username and session_key in config file config/secrets.yml"
            )
            self._network.session_key = self._session_key = result["session_key"]
            self._network.username = self._username = result["username"]
        else:
            logger.warning(
                "No entry found of username and session_key in config file config/secrets.yml"
            )
            self._session_key: str = None
            self._username: str = None
            return False
        return True

    def request_user_access(self, username: str) -> dict:
        """Prompt your user to "accept" the terms of your application. The application
        will act on behalf of their discogs.com account."""
        self._username = username
        url = self._session_key_gen.get_web_auth_url()
        return {
            "message": "Authorize BoelMuziek for access to your Last.fm account :",
            "url": url,
        }

    def await_authorization(self, url):
        while True:
            try:
                session_key = self._session_key_gen.get_web_auth_session_key(url)
                break
            except pylast.WSError:
                time.sleep(1)
        self._network.session_key = self._secrets["session_key"] = session_key
        self._network.username = self._secrets["username"] = self._username
        self._user_secrets_file.write_secrets(dict_secrets=self._secrets)
        return {"key": session_key}

    def save_session_key(self, session_key: str, username: str) -> dict:
        logger.info("Receiving confirmation of access to the user's Last.fm account")
        self._network.session_key = self._secrets["session_key"] = session_key
        self._network.username = self._secrets["username"] = username
        self._user_secrets_file.write_secrets(dict_secrets=self._secrets)
        return {"status_code": 200, "message": "User connected."}

    def get_artist_bio(self, name_artist: str) -> str:
        logger.info(f"Retrieving artist bio of {name_artist}")
        print(self._network.session_key)
        artist = self._network.get_artist(artist_name=name_artist)
        try:
            bio = artist.get_bio_content()
        except pylast.WSError as e:
            print(e)
            bio = None
        return bio

    def scrobble_track(
        self, name_artist: str, name_song: str, name_album: str = None
    ) -> None:
        now = int(time.time())
        logger.info(f"Scrobbling {name_artist}-{name_song} to Last.fm")
        try:
            self._network.scrobble(
                artist=name_artist, title=name_song, album=name_album, timestamp=now
            )
        except pylast.NetworkError as e:
            logger.error(
                f"Failed to scrobble '{name_artist}-{name_song}' due to {e.underlying_error}"
            )

    def now_playing_track(
        self, name_artist: str, name_song: str, name_album: str = None
    ) -> None:
        logger.info(f"Set 'now playing' {name_artist}-{name_song} to Last.fm")
        try:
            self._network.update_now_playing(
                artist=name_artist, title=name_song, album=name_album
            )
        except pylast.NetworkError as e:
            logger.error(
                f"Failed to set Now Playing for '{name_artist}-{name_song}' due to {e.underlying_error}"
            )

    def love_track(self, name_artist: str, name_song: str) -> bool:
        logger.info(f"Loving {name_artist}-{name_song} on Last.fm")
        try:
            track = self._network.get_track(artist=name_artist, title=name_song)
            track.love()
            return True
        except pylast.NetworkError as e:
            logger.error(
                f"Failed to set love for '{name_artist} - {name_song}' due to {e.underlying_error}"
            )
            return False
        except pylast.WSError:
            logger.error(
                f"Failed to set love for '{name_artist} - {name_song}' due to authorization issues, re-authenticate."
            )
            return False

    def get_loved_tracks(self, limit: int) -> list:
        logger.info(f"Get {self._network.username}'s loved tracks")
        user = self._network.get_authenticated_user()
        lst_tracks = user.get_loved_tracks(limit=limit)
        lst_loved_tracks = []
        for track in lst_tracks:
            lst_loved_tracks.append(
                {
                    "datetime": parser.parse(track.date),
                    "timestamp": int(track.timestamp),
                    "name_song": track.track.title,
                    "name_artist": track.track.artist.name,
                }
            )
        return lst_loved_tracks

    def get_top_assets(
        self, type_asset: str, limit: int, period: str = "overall"
    ) -> dict:
        user = self._network.get_user(username=self._username)
        lst_results = []
        try:
            if type_asset == "artists":
                top_items = user.get_top_artists(period=period, limit=limit)
            elif type_asset == "albums":
                top_items = user.get_top_albums(period=period, limit=limit)
            elif type_asset == "songs":
                top_items = user.get_top_tracks(period=period, limit=limit)
        except pylast.NetworkError as e:
            logger.error(f"Failed to get Top Albums because of {e}")
        for top_item in top_items:
            if type_asset == "artists":
                dict_top_item = {
                    "name_artist": top_item.item.name,
                    "qty_plays": int(top_item.weight),
                }
            elif type_asset == "albums":
                dict_top_item = {
                    "name_artist": top_item.item.artist.name,
                    "name_album": top_item.item.title,
                    "qty_plays": int(top_item.weight),
                }
            elif type_asset == "songs":
                dict_top_item = {
                    "name_artist": top_item.item.artist.name,
                    "name_song": top_item.item.title,
                    "qty_plays": int(top_item.weight),
                }
            lst_results.append(dict_top_item)
        return lst_results
