from pathlib import Path
import os
import pylast

import mpd_client
from secrets_yaml import SecretsYAML

class LastFm:
    def __init__(self) -> None:
        self._secrets = {'user_token': ''}
        self._user_secrets_file = SecretsYAML(
            file_path='config/secrets.yml',
            app='lastfm',
            expected_keys=set(self._secrets.keys())
            )
        self._api_key = 'e62c2f9c25ed0ee24bd8e21857f61899'
        self._api_secret = 'a4d7454f18985649f30fc67602d592ed'
        self._network = pylast.LastFMNetwork(self._api_key, self._api_secret)
        self._callback_auth = 'http://localhost:5080/lastfm/receive-token'

    def check_user_token(self):
        result = self._user_secrets_file.read_secrets()
        if result is not None:
            self._network.session_key = result['user_token']
            user = self._network.get_authenticated_user()
        else:
            return False

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
        user = self._network.get_authenticated_user()
        return { 'status_code': 200, 'message': f"User {user} accepted."}




