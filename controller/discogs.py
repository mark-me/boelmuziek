import os
import yaml

import discogs_client
from discogs_client.exceptions import HTTPError

class Discogs:
    def __init__(self) -> None:
        self.consumer_key = 'zvHFpFQWJrdDfCwoLalG'
        self.consumer_secret = 'FzRxDEGBbvWZpAmkQKBYHYeNdIjKxnVO'
        self.file_secrets = 'secrets.yml'
        self.user_token: str = None
        self.user_secret: str = None
        self.user: str = None
        self.user_name: str=None
        # A user-agent is required with Discogs API requests. Be sure to make your
        # user-agent unique, or you may get a bad response.
        self.user_agent = 'boelmuziek'
        self.discogsclient = discogs_client.Client(self.user_agent,
                                                    consumer_key=self.consumer_key,
                                                    consumer_secret=self.consumer_secret)
        if self.has_user_tokens()['status'] == 200:
            self.load_user_secrets()

    def has_user_tokens(self) -> dict:
        """ Checks if user secrets are already present"""
        if not os.path.isfile(self.file_secrets):
            return {'status': 500,
                    'message': 'File does not exist'}

        # Load the YAML file
        with open(self.file_secrets, 'r') as file:
            try:
                yaml_data = yaml.safe_load(file)
            except yaml.YAMLError as e:
                return {'status': 500,
                        'message': f"Error loading YAML file: {str(e)}" }
        if not isinstance(yaml_data, dict):
            return {'status': 500,
                    'message': 'YAML file does not contain a dictionary' }
        # Check if 'token' and 'secret' keys are present
        expected_keys = {'token', 'secret'}
        missing_keys = expected_keys - set(yaml_data.keys())
        if missing_keys:
            return {'status': 500,
                    'message': f"Missing keys in YAML file: {', '.join(missing_keys)}" }
        return {'status': 200,
                'message': 'YAML file is valid'}

    def load_user_secrets(self) -> dict:
        with open(self.file_secrets, 'r') as file:
            try:
                data = yaml.safe_load(file)
                self.user_secret = data['secret']
                self.user_token = data['token']
                self.user = data['user']
                self.user_name = data['name']
            except yaml.YAMLError as e:
                return {'status': 500,
                        'message': f"Error loading YAML file: {str(e)}"}
        self.discogsclient.set_token(token=self.user_token, secret=self.user_secret)
        try:
            self.discogsclient.identity()
        except HTTPError:
                return {'status': 401, 'message': 'Unable to authenticate.'}
        return {'status': 200,
                'message': 'Loaded user credentials'}

    def request_user_access(self) -> dict:
        """ Prompt your user to "accept" the terms of your application. The application
            will act on behalf of their discogs.com account."""
        self.user_token, self.user_secret, url = self.discogsclient.get_authorize_url()
        return {'message': 'Authorize BoelMuziek for access to your Discogs account :',
                'url': url}

    def validate_verification_code(self, verification_code: str) -> dict:
        """If the user accepts, discogs displays a key to the user that is used for
            verification. The key is required in the 2nd phase of authentication."""
        oauth_verifier = verification_code
        try:
            self.user_token, self.user_secret = self.discogsclient.get_access_token(oauth_verifier)
        except HTTPError:
            return {'status': 401, 'message': 'Unable to authenticate.'}
        user = self.discogsclient.identity() # Fetch the identity object for the current logged in user.
        # Write to secrets file
        dict_user = {
            'token': self.user_token,
            'secret': self.user_secret,
            'user': user.username,
            'name': user.name
        }
        with open(self.file_secrets, 'w') as file:
            yaml.dump(dict_user, file)
        self.load_user_secrets()
        return {'status': 200, 'message': 'Verification complete'}

    def get_artist_image(self, name_artist: str):
        search_results = self.discogsclient.search(name_artist, type='artist')
        image = search_results[0].images[0]['uri']
        content, resp = self.discogsclient._fetcher.fetch(None, 'GET', image,
                                                          headers={'User-agent': self.user_agent})
        return {'status': resp,
                'message': content}


if __name__ == "__main__":
    # Example flow for authentication
    discogs = Discogs()
    has_tokens = discogs.has_user_tokens()
    if not has_tokens['status'] == 200:
        dict_msg = discogs.request_user_access()
        print(dict_msg['message'])
        print(dict_msg['url'])
        verification_code = input("Verification code: ")
        discogs.validate_verification_code(verification_code=verification_code)
    else:
        discogs.load_user_secrets()

    response = discogs.get_artist_image('Tom Waits')
    print("test")
    # if :
    #     dict_secrets = discogs.load_user_secrets()
    # else: