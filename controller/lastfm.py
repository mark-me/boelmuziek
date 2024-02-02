import asyncio
import time
import pylast
import os
import sys

from mpd_client import *
from secrets_yaml import SecretsYAML

class LastFm:
    def __init__(self) -> None:
        self._callback_auth = 'http://localhost:5080/lastfm/receive-token'
        dir_cur_working = os.getcwd()
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
        url = "http://www.last.fm/api/auth/?api_key=" + self._api_key +"&cb=" + self._callback_auth
        return {'message': 'Authorize BoelMuziek for access to your Last.fm account :',
                'url': url}

    def save_user_token(self, auth_token: str) -> dict:
        self._secrets['user_token'] = auth_token
        self._user_secrets_file.write_secrets(dict_secrets=self._secrets)
        self._network.session_key = auth_token
        return { 'status_code': 200, 'message': f"User connected."}

    def get_artist_art(self, name_artist: str) -> str:
        artist = self._network.get_artist(artist_name=name_artist)
        track = self._network.get_track("Iron Maiden", "The Nomad")
        info_artist = artist.get_mbid()
        return { 'MusicBrainzID': info_artist }

    def scrobble_track(self, name_artist: str, name_song: str, name_album: str=None) -> None:
        now = int(time.time())
        self._network.scrobble(artist=name_artist, title=name_song, album=name_album, timestamp=now)

    def love_track(self, name_artist: str, name_song: str) -> None:
        track = self._network.get_track(artist=name_artist, title=name_song)
        track.love()

    async def loop_scrobble(self) -> None:
        """A loop for scrobbling
        """
        mpd = MPDController(host='localhost')
        is_connected = await mpd.connect()

        currently_playing :dict = None
        while is_connected:
            async for result in mpd.mpd_client.idle(['player']):

                if currently_playing is not None:
                    self.scrobble_track(
                        name_artist=currently_playing['artist'],
                        name_song=currently_playing['song'],
                        name_album=currently_playing['album']
                        )

                currently_playing = await mpd.current_song()
                if 'album' not in currently_playing.keys():
                    currently_playing['album'] = None

                self._network.update_now_playing(
                    artist=currently_playing['artist'],
                    title=currently_playing['song'],
                    album=currently_playing['album']
                    )


if __name__ == "__main__":
    lastfm = LastFm()
    if not lastfm.check_user_token():
        print("Not authenticated with Last.fm. Use API to login.\nTerminating.")
        sys.exit(0)
    asyncio.run(lastfm.loop_scrobble())
