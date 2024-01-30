import os
import yaml

import discogs_client
from discogs_client.exceptions import HTTPError

class Discogs:
    def __init__(self) -> None:
        self._consumer_key = 'zvHFpFQWJrdDfCwoLalG'
        self._consumer_secret = 'FzRxDEGBbvWZpAmkQKBYHYeNdIjKxnVO'
        self._file_secrets = 'secrets.yml'
        self._user_token: str = None
        self._user_secret: str = None
        self._user: str = None
        self._user_name: str=None
        # A user-agent is required with Discogs API requests. Be sure to make your
        # user-agent unique, or you may get a bad response.
        self.user_agent = 'boelmuziek'
        self.discogsclient = discogs_client.Client(self.user_agent,
                                                    consumer_key=self._consumer_key,
                                                    consumer_secret=self._consumer_secret)
        if self.has_user_tokens()['status_code'] == 200:
            self.load_user_secrets()

    @property
    def user_token(self):
        return self._user_token

    @property
    def user_secret(self):
        return self._user_secret

    def has_user_tokens(self) -> dict:
        """ Checks if user secrets are already present"""
        if not os.path.isfile(self._file_secrets):
            return {'status_code': 500,
                    'detail': 'There is no config file for secrets'}

        # Load the YAML file
        with open(self._file_secrets, 'r') as file:
            try:
                yaml_data = yaml.safe_load(file)
            except yaml.YAMLError as e:
                return {'status_code': 500,
                        'detail': f"Error loading YAML file: {str(e)}"}
        if not isinstance(yaml_data, dict):
            return {'status_code': 500,
                    'detail': 'YAML file does not contain a dictionary'}
        # Check if 'token' and 'secret' keys are present
        expected_keys = {'token', 'secret'}
        missing_keys = expected_keys - set(yaml_data.keys())
        if missing_keys:
            return{'status_code': 500,
                   'detail': f"Missing keys in YAML file: {', '.join(missing_keys)}"}
        return {'status_code':200,
                'detail':'YAML file is valid'}

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
