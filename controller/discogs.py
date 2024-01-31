import os
import yaml
from pathlib import Path

import discogs_client
from discogs_client.exceptions import HTTPError
from secrets_yaml import SecretsYAML

class Discogs:
    def __init__(self) -> None:
        self._consumer_key = 'zvHFpFQWJrdDfCwoLalG'
        self._consumer_secret = 'FzRxDEGBbvWZpAmkQKBYHYeNdIjKxnVO'
        self._secrets = {'user_token': 'user_secret'}
        self._user_secrets_file = SecretsYAML(
            file_path='config/secrets.yml',
            app='discogs',
            expected_keys=set(self._secrets.keys())
            )
        self.user_agent = 'boelmuziek'
        self.discogsclient = discogs_client.Client(self.user_agent,
                                                   consumer_key=self._consumer_key,
                                                   consumer_secret=self._consumer_secret)
        # if self.has_user_tokens():
        #     self.load_user_secrets()

    @property
    def user_token(self):
        return self._user_token

    @property
    def user_secret(self):
        return self._user_secret

    def has_user_tokens(self) -> dict:
        result = self._user_secrets_file.read_secrets()
        if result is not None:
            self.discogsclient.set_token(token=result['user_token'], secret=result['user_secret'])
            user = self._network.get_authenticated_user()
        else:
            return False

    def load_user_secrets(self) -> dict:
        """Load user secrets from file and reports on success

        Returns:
            dict: Report of sucess
        """
        with open(self._file_secrets, 'r') as file:
            try:
                data = yaml.safe_load(file)
                self._user_secret = data['secret']
                self._user_token = data['token']
                self._user = data['user']
                self._user_name = data['name']
            except yaml.YAMLError as e:
                return {'status_code': 500,
                        'detail': f"Error loading YAML file: {str(e)}"}
        self.discogsclient.set_token(token=self._user_token, secret=self._user_secret)
        try:
            self.discogsclient.identity()
        except HTTPError:
            return {'status_code': 401,
                    'detail': 'Unable to authenticate.'}
        return {'status_code': 200,
                'detail': 'Loaded user credentials'}

    def request_user_access(self, callback_url: str=None) -> dict:
        """ Prompt your user to "accept" the terms of your application. The application
            will act on behalf of their discogs.com account."""
        self._user_token, self._user_secret, url = self.discogsclient.get_authorize_url(callback_url=callback_url)
        return {'message': 'Authorize BoelMuziek for access to your Discogs account :',
                'url': url}

    def validate_verification_code(self, verification_code: str) -> dict:
        """If the user accepts, discogs displays a key to the user that is used for
            verification. The key is required in the 2nd phase of authentication."""
        oauth_verifier = verification_code
        try:
            self._user_token, self._user_secret = self.discogsclient.get_access_token(oauth_verifier)
        except HTTPError:
            return{'status_code': 401,
                   'detail': 'Unable to authenticate.'}
        user = self.discogsclient.identity() # Fetch the identity object for the current logged in user.
        # Write to secrets file
        dict_user = {
            'token': self._user_token,
            'secret': self._user_secret,
            'user': user.username,
            'name': user.name
        }
        with open(self._file_secrets, 'w') as file:
            yaml.dump(dict_user, file)
        self.load_user_secrets()
        return {'status_code': 200, 'detail': 'Verification complete'}

    def get_artist_image(self, name_artist: str):
        search_results = self.discogsclient.search(name_artist, type='artist')
        if search_results == None:
            return{'status_code': 404,
                   'detail': f"Artist not found: {name_artist}"}
        else:
            try:
                image = search_results[0].images[0]['uri']
                content, resp = self.discogsclient._fetcher.fetch(None, 'GET', image,
                                                                  headers={'User-agent': self.user_agent})
            except TypeError:
                return {'status_code': 404,
                        'detail': f"No artist image found : {name_artist}"}
            return {'status': resp,
                    'message': content}
