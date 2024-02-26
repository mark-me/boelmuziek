from hashlib import md5
import json
import logging
import os
import sys
import time

from dotenv import dotenv_values
from dateutil import parser
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


class LastFm:
    def __init__(self) -> None:
        self._api_key = "2e031e7b2ab98c1bce14436016185a4d"
        self._shared_secret = "fcce22fac65bcdcfcc249841f4ffed8b"
        self._client = api.LastFMApi(
            api_key=self._api_key,
            shared_secret=self._shared_secret
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

    def __get_signature(self, api_method: str) -> str:
        signature = f"api_key{self._api_key}methodauth.getSessiontoken{self._token}{self._shared_secret}"
        h = md5()
        h.update(signature.encode())
        hash_signature = h.hexdigest()
        return hash_signature

    def request_session_key(self):
        hash_signature = self.__get_signature()
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

    def get_artist_bio(self, name_artist: str) -> str:
        response: str = self._client.post(
            method=methods.Artist.GET_INFO,
            params=params.ArtistGetInfo(artist=name_artist),
            additional_params=dict(format="json"),
        )
        artist = json.loads(response)["artist"]
        return artist["bio"]["content"]

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
                f"Failed to set Now Playing for '{name_artist} - {name_song}' due to {e.underlying_error}"
            )

    def __signature(self) -> str:
        signature = f"api_key{self._api_key}methodtrack.lovesk{self._session_key}{self._shared_secret}"
        data = {
            "api_key": self._api_key,
            "method": "track.love",
            "track" : "Cabin in My Mind",
            "artist" :"Grandaddy",
            "sk" : self._session_key
            }
        keys = sorted(data.keys())
        param = [k+data[k] for k in keys]
        param = "".join(param) + self._shared_secret
        api_sig = md5(param.encode()).hexdigest()
        return api_sig

    def love_track(self, name_artist: str, name_song: str) -> bool:
        logger.info(f"Loving {name_artist} - {name_song} on Last.fm")
        signature = self.__signature()
        result = self._client.post(
            method=methods.Track.LOVE,
            params=params.TrackLove(
                artist=name_artist,
                track=name_song,
                api_key=self._api_key,
                api_sig=signature,
                sk=self._session_key,
            ),
            additional_params=dict(format="json"),
        )
        return result

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
        self, type_asset: str, period: str = "overall", page: int = 1
    ) -> dict:
        lst_results = []

        if type_asset == "artists":
            response: str = self._client.post(
                method=methods.User.GET_TOP_ARTISTS,
                params=params.UserGetTopArtists(
                    user=self._username, period=period, page=page
                ),
                additional_params=dict(format="json"),
            )
            top_items = json.loads(response)
            top_items = top_items["topartists"]["artist"]
        elif type_asset == "albums":
            response: str = self._client.post(
                method=methods.User.GET_TOP_ALBUMS,
                params=params.UserGetTopAlbums(
                    user=self._username, period=period, page=page
                ),
                additional_params=dict(format="json"),
            )
            top_items = json.loads(response)
            top_items = top_items["topalbums"]["album"]
        elif type_asset == "songs":
            response: str = self._client.post(
                method=methods.User.GET_TOP_TRACKS,
                params=params.UserGetTopTracks(
                    user=self._username, period=period, page=page
                ),
                additional_params=dict(format="json"),
            )
            top_items = json.loads(response)
            top_items = top_items["toptracks"]["track"]
        if len(top_items) == 0:
            return [
                {
                    "status_code": 404,
                    "details": f"No more {type_asset} for the period {period} results on page {page}",
                }
            ]
        for top_item in top_items:
            if type_asset == "artists":
                dict_top_item = {
                    "name_artist": top_item["name"],
                    "qty_plays": int(top_item["playcount"]),
                }
            elif type_asset == "albums":
                dict_top_item = {
                    "name_artist": top_item["artist"]["name"],
                    "name_album": top_item["name"],
                    "qty_plays": int(top_item["playcount"]),
                }
            elif type_asset == "songs":
                dict_top_item = {
                    "name_artist": top_item["artist"]["name"],
                    "name_song": top_item["name"],
                    "qty_plays": int(top_item["playcount"]),
                }
            lst_results.append(dict_top_item)
        return lst_results

    def get_recent_songs(self, page: int = 1):
        lst_songs = []
        response: str = self._client.post(
            method=methods.User.GET_RECENT_TRACKS,
            params=params.UserGetRecentTracks(
                user=self._username, page=page, extended=True
            ),
            additional_params=dict(format="json"),
        )
        recent_songs = json.loads(response)
        recent_songs = recent_songs["recenttracks"]["track"]
        for recent_song in recent_songs:
            lst_songs.append(
                {
                    "name_artist": recent_song["artist"]["name"],
                    "name_song": recent_song["name"],
                    "dt_played": parser.parse(recent_song["date"]["#text"]),
                }
            )
        return lst_songs


if __name__ == "__main__":
    lstfm = LastFm()
    result = lstfm.love_track(name_artist="Grandaddy", name_song="Cabin in My Mind")
