from hashlib import md5
import json
import logging
import os
import sys

from dotenv import dotenv_values
from lastfmxpy import (
    api,
    methods,
    params,
)

sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")

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


class LastFmClient:
    def __init__(self) -> None:
        self._api_key = "2e031e7b2ab98c1bce14436016185a4d"
        self._shared_secret = "fcce22fac65bcdcfcc249841f4ffed8b"
        self._client = api.LastFMApi(
            api_key=self._api_key, shared_secret=self._shared_secret
        )
        self._secrets = {"session_key": "", "username": ""}
        self._user_secrets_file = SecretsYAML(
            file_path="config/secrets.yml",
            app="lastfm",
            expected_keys=set(self._secrets.keys()),
        )
        self._session_key = self._username = None
        self.check_user_data()

    def check_user_data(self):
        result = self._user_secrets_file.read_secrets()
        if result is not None:
            logger.info(
                "Found username and session_key in config file config/secrets.yml"
            )
            self._session_key = result["session_key"]
            self._username = result["username"]
        else:
            logger.warning(
                "No entry found of username and session_key in config file config/secrets.yml"
            )
            self._session_key: str = None
            self._username: str = None
            return False
        return True

    def request_authorization(self):
        response: str = self._client.post(
            method=methods.Auth.GET_TOKEN,
            params=params.AuthGetToken(
                api_key=self._api_key,
            ),
            additional_params=dict(format="json"),
        )
        self._token = json.loads(response)["token"]
        url = (
            f"http://www.last.fm/api/auth/?api_key={self._api_key}&token={self._token}"
        )
        return url

    def __get_auth_signature(self, api_method: str) -> str:
        signature = f"api_key{self._api_key}methodauth.getSessiontoken{self._token}{self._shared_secret}"
        h = md5()
        h.update(signature.encode())
        hash_signature = h.hexdigest()
        return hash_signature

    def request_session_key(self):
        hash_signature = self.__get_auth_signature()
        dict_response = {"error": 13}
        while "error" in dict_response.keys():
            response: str = self._client.post(
                method=methods.Auth.GET_SESSION,
                params=params.AuthGetSession(
                    token=self._token, api_key=self._api_key, api_sig=hash_signature
                ),
                additional_params=dict(format="json"),
            )
            dict_response = json.loads(response)

        self._session_key = dict_response["session"]["key"]
        self._username = dict_response["session"]["name"]
        self._secrets = {
            "session_key": self._session_key,
            "username": self._username,
        }
        self._user_secrets_file.write_secrets(dict_secrets=self._secrets)
        return response

    def signature(self, dict_params: dict) -> str:
        keys = sorted(dict_params.keys())
        param = [k + dict_params[k] for k in keys]
        param = "".join(param) + self._shared_secret
        api_sig = md5(param.encode()).hexdigest()
        return api_sig


if __name__ == "__main__":
    lstfm = LastFmClient()
    result = lstfm.get_recent_songs(time_to="1394059277")
    print(result)
