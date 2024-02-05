import pylast
from dotenv import dotenv_values

import time
import os
import logging

from utils import SecretsYAML

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

logging.basicConfig(
    format='%(levelname)s:\t%(asctime)s - %(module)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class LastFm:
    def __init__(self, host: str, port: int) -> None:
        self._secrets = {'user_token': ''}
        self._user_secrets_file = SecretsYAML(
            file_path='config/secrets.yml',
            app='lastfm',
            expected_keys=set(self._secrets.keys())
            )
        self._api_key = 'e62c2f9c25ed0ee24bd8e21857f61899'
        self._api_secret = 'a4d7454f18985649f30fc67602d592ed'
        secrets = self._user_secrets_file.read_secrets()
        if secrets is None or (not 'user_token' in secrets.keys()):
            self._session_key :str= None
        elif 'user_token' in secrets.keys():
            self._session_key = secrets['user_token']
        self._network = pylast.LastFMNetwork(api_key=self._api_key,
                                             api_secret=self._api_secret,
                                             session_key=self._session_key
                                             )

    def check_user_token(self):
        result = self._user_secrets_file.read_secrets()
        if result is not None:
            logger.info("Found user token in config file config/secrets.yml")
            self._network.session_key = result['user_token']
        else:
            return False
        return True

    # def request_user_access(self, callback_url: str=None) -> dict:
    #     """ Prompt your user to "accept" the terms of your application. The application
    #         will act on behalf of their discogs.com account."""
    #     skg = pylast.SessionKeyGenerator(self._network)
    #     url = skg.get_web_auth_url()
    #     import webbrowser
    #     webbrowser.open(url)
    #     while True:
    #         try:
    #             session_key = skg.get_web_auth_session_key(url)
    #             break
    #         except pylast.WSError:
    #             time.sleep(1)
    #     self._secrets['user_token'] = session_key
    #     self._user_secrets_file.write_secrets(dict_secrets=self._secrets)
    #     self._network.session_key = session_key
    #     return {'key': session_key}

    def request_user_access(self, callback_url: str=None) -> dict:
        """ Prompt your user to "accept" the terms of your application. The application
            will act on behalf of their discogs.com account."""
        logger.info(f"Requesting the user access to her/his Last.fm account with callback_url {callback_url}")
        url = f"http://www.last.fm/api/auth/?api_key={self._api_key}&cb={callback_url}"
        return {'message': 'Authorize BoelMuziek for access to your Last.fm account :',
                'url': url}

    def save_user_token(self, auth_token: str) -> dict:
        logger.info("Receiving confirmation of access to the user\'s Last.fm account")
        self._secrets['user_token'] = auth_token
        self._user_secrets_file.write_secrets(dict_secrets=self._secrets)
        self._network.session_key = auth_token
        return { 'status_code': 200, 'message': f"User connected."}

    def get_artist_bio(self, name_artist: str) -> str:
        logger.info(f"Retrieving artist bio of {name_artist}")
        artist = self._network.get_artist(artist_name=name_artist)
        bio = artist.get_bio_content()
        return bio

    def scrobble_track(self, name_artist: str, name_song: str, name_album: str=None) -> None:
        now = int(time.time())
        logger.info(f"Scrobbling {name_artist}-{name_song} to Last.fm")
        try:
            self._network.scrobble(artist=name_artist, title=name_song, album=name_album, timestamp=now)
        except pylast.NetworkError as e:
            logger.error(f"Failed to scrobble \'{name_artist}-{name_song}\' due to {e.underlying_error}")

    def now_playing_track(self, name_artist: str, name_song: str, name_album: str=None) -> None:
        logger.info(f"Set 'now playing' {name_artist}-{name_song} to Last.fm")
        try:
            self._network.update_now_playing(artist=name_artist, title=name_song, album=name_album)
        except pylast.NetworkError as e:
            logger.error(f"Failed to set Now Playing for \'{name_artist}-{name_song}\' due to {e.underlying_error}")

    def love_track(self, name_artist: str, name_song: str) -> None:
        logger.info(f"Loving {name_artist}-{name_song} on Last.fm")
        try:
            track = self._network.get_track(artist=name_artist, title=name_song)
            track.love()
        except pylast.NetworkError as e:
            logger.error(f"Failed to set love for \'{name_artist}-{name_song}\' due to {e.underlying_error}")

    def get_top_albums(self, period: str='overall', page: int=1) -> dict:
        user = self._network.get_user(username='schizelmizels')
        #user = self._network.get_authenticated_user()
        #test = user.get_name()
        lst_albums = []
        try:
            top_items = user.get_top_albums()
        except pylast.NetworkError as e:
            logger.error(f"Failed to get Top Albums because of {e}")
        for top_item in top_items:
            lst_albums.append({'name_artist': top_item.item.artist.name, 'name_album': top_item.item.title, 'qty_plays': top_item.weight})

        return lst_albums



