import logging

from lastfmxpy import (
    methods,
    params,
)

from controller.lastfm.lastfm_client import LastFmClient

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class LastFmSubmit(LastFmClient):
    def __init__(self) -> None:
        super(LastFmSubmit, self).__init__()

    def love_track(self, name_artist: str, name_song: str) -> bool:
        logger.info(f"Loving {name_artist} - {name_song} on Last.fm")
        dict_params = {
            "api_key": self._api_key,
            "method": "track.love",
            "track": name_song,
            "artist": name_artist,
            "sk": self._session_key,
        }
        signature = self.signature(dict_params=dict_params)
        result = self._client.post(
            method=methods.Track.LOVE,
            params=params.TrackLove(
                artist=dict_params["artist"],
                track=dict_params["track"],
                api_key=dict_params["api_key"],
                api_sig=signature,
                sk=dict_params["sk"],
            ),
            additional_params=dict(format="json"),
        )
        return result

    def unlove_track(self, name_artist: str, name_song: str) -> bool:
        logger.info(f"Loving {name_artist} - {name_song} on Last.fm")
        dict_params = {
            "api_key": self._api_key,
            "method": "track.unlove",
            "track": name_song,
            "artist": name_artist,
            "sk": self._session_key,
        }
        signature = self.signature(dict_params=dict_params)
        result = self._client.post(
            method=methods.Track.UNLOVE,
            params=params.TrackUnlove(
                artist=dict_params["artist"],
                track=dict_params["track"],
                api_key=dict_params["api_key"],
                api_sig=signature,
                sk=dict_params["sk"],
            ),
            additional_params=dict(format="json"),
        )
        return result
