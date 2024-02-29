import logging
import time

from lastfmxpy import (
    methods,
    params,
)

from lastfm.lastfm_client import LastFmClient

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class LastFmListening(LastFmClient):
    def __init__(self) -> None:
        super(LastFmListening, self).__init__()

    def scrobble_track(
        self, name_artist: str, name_song: str, name_album: str = None
    ) -> None:
        now = int(time.time())
        logger.info(f"Scrobbling {name_artist} - {name_song} to Last.fm")
        dict_params = {
            "api_key": self._api_key,
            "method": "track.scrobble",
            "track": name_song,
            "artist": name_artist,
            "sk": self._session_key,
            "timestamp": str(now),
        }
        if name_album is not None:
            dict_params["album"] = name_album
        signature = self.signature(dict_params=dict_params)
        if name_album is not None:
            result = self._client.post(
                method=methods.Track.SCROBBLE,
                params=params.TrackScrobble(
                    artist=dict_params["artist"],
                    album=dict_params["album"],
                    track=dict_params["track"],
                    api_key=dict_params["api_key"],
                    api_sig=signature,
                    sk=dict_params["sk"],
                    timestamp=now,
                ),
                additional_params=dict(format="json"),
            )
        else:
            result = self._client.post(
                method=methods.Track.SCROBBLE,
                params=params.TrackScrobble(
                    artist=dict_params["artist"],
                    track=dict_params["track"],
                    api_key=dict_params["api_key"],
                    api_sig=signature,
                    sk=dict_params["sk"],
                    timestamp=dict_params["timestamp"],
                ),
                additional_params=dict(format="json"),
            )
        return result

    def now_playing_track(
        self, name_artist: str, name_song: str, name_album: str = None
    ) -> None:
        logger.info(f"Set 'now playing' {name_artist}-{name_song} to Last.fm")
        dict_params = {
            "api_key": self._api_key,
            "method": "track.updateNowPlaying",
            "album": name_album,
            "track": name_song,
            "artist": name_artist,
            "sk": self._session_key
        }
        signature = self.signature(dict_params=dict_params)
        result = self._client.post(
            method=methods.Track.UPDATE_NOW_PLAYING,
            params=params.TrackUpdateNowPlaying(
                artist=dict_params["artist"],
                album=dict_params["album"],
                track=dict_params["track"],
                api_key=dict_params["api_key"],
                sk=dict_params["sk"],
                api_sig=signature
            ),
            additional_params=dict(format="json"),
        )
        return result
