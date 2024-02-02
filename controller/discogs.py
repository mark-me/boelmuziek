from pathlib import Path
import time
import discogs_client
from discogs_client.exceptions import HTTPError
from secrets_yaml import SecretsYAML

class Discogs:
    def __init__(self) -> None:
        self._consumer_key = 'zvHFpFQWJrdDfCwoLalG'
        self._consumer_secret = 'FzRxDEGBbvWZpAmkQKBYHYeNdIjKxnVO'
        self._secrets = {'name': None, 'secret': None, 'token': None, 'user': None}
        self._user_secrets_file = SecretsYAML(
            file_path='config/secrets.yml',
            app='discogs',
            expected_keys=set(self._secrets.keys())
            )
        self.user_agent = 'boelmuziek'
        self.discogsclient = discogs_client.Client(self.user_agent,
                                                   consumer_key=self._consumer_key,
                                                   consumer_secret=self._consumer_secret)
        self.check_user_tokens()

    @property
    def user_token(self):
        return self._user_token

    @property
    def user_secret(self):
        return self._user_secret

    def check_user_tokens(self) -> dict:
        result = self._user_secrets_file.read_secrets()
        if result is not None:
            self.discogsclient.set_token(token=result['token'], secret=result['secret'])
        else:
            return False

    def request_user_access(self, callback_url: str=None) -> dict:
        """ Prompt your user to "accept" the terms of your application. The application
            will act on behalf of their discogs.com account."""
        self._user_token, self._user_secret, url = self.discogsclient.get_authorize_url(callback_url=callback_url)
        return {'message': 'Authorize BoelMuziek for access to your Discogs account :',
                'url': url}

    def save_user_token(self, verification_code: str) -> dict:
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
        self._user_secrets_file.write_secrets(dict_secrets=dict_user)
        return { 'status_code': 200, 'message': f"User {user.username} connected."}

    def get_artist_image(self, name_artist: str) -> dict:
        path_image = f"artist_images/{name_artist}.jpg"

        # Load cached image
        if Path(path_image).is_file():
            with open(path_image, 'rb') as file:
                content = file.read()
            return {'status': 200,
                    'message': content}

        # Fetch image from discogs
        try:
            search_results = self.discogsclient.search(name_artist, type='artist')
        except HTTPError as e:
            if e.status_code == 429:
                time.sleep(60)

        if search_results == None:
            return{'status_code': 404,
                   'detail': f"Artist not found: {name_artist}"}
        else:
            try:
                image = search_results[0].images[0]['uri']
                content, resp = self.discogsclient._fetcher.fetch(None, 'GET', image,
                                                                  headers={'User-agent': self.user_agent})
                # Write artist image to cache
                with open(path_image, "wb") as file:
                    file.write(content)
            except (TypeError, IndexError):
                return {'status_code': 404,
                        'detail': f"No artist image found : {name_artist}"}
            except HTTPError as e:
                if e.status_code == 429:
                    time.sleep(60)
            return {'status': resp,
                    'message': content}

    def artist_images_bulk(self, list_artists: list) -> None:
        for artist in list_artists:
            self.get_artist_image(name_artist=artist.artist)