
import logging
import os
import time
import json

from dotenv import dotenv_values
from dateutil import parser
from lastfmxpy import (
    api,
    methods,
    params,
)

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
        self._client = api.LastFMApi(
            api_key="2e031e7b2ab98c1bce14436016185a4d",
            shared_secret="fcce22fac65bcdcfcc249841f4ffed8b"
        )

    def get_artist_bio(self, name_artist: str) -> str:
        response: str = self._client.post(
            method=methods.Artist.GET_INFO,
            params=params.ArtistGetInfo(artist=name_artist),
            additional_params=dict(format="json")
        )
        artist = json.loads(response)['artist']
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
                f"Failed to set Now Playing for '{name_artist}-{name_song}' due to {e.underlying_error}"
            )

    def love_track(self, name_artist: str, name_song: str) -> bool:
        logger.info(f"Loving {name_artist}-{name_song} on Last.fm")
        try:
            track = self._network.get_track(artist=name_artist, title=name_song)
            track.love()
            return True
        except pylast.NetworkError as e:
            logger.error(
                f"Failed to set love for '{name_artist} - {name_song}' due to {e.underlying_error}"
            )
            return False
        except pylast.WSError:
            logger.error(
                f"Failed to set love for '{name_artist} - {name_song}' due to authorization issues, re-authenticate."
            )
            return False

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
        self, type_asset: str, limit: int, period: str = "overall"
    ) -> dict:
        user = self._network.get_user(username=self._username)
        lst_results = []
        try:
            if type_asset == "artists":
                top_items = user.get_top_artists(period=period, limit=limit)
            elif type_asset == "albums":
                top_items = user.get_top_albums(period=period, limit=limit)
            elif type_asset == "songs":
                top_items = user.get_top_tracks(period=period, limit=limit)
        except pylast.NetworkError as e:
            logger.error(f"Failed to get Top Albums because of {e}")
            return {'status_code': 408, 'details': f"Failed to get Top Albums because of {e}"}
        for top_item in top_items:
            if type_asset == "artists":
                dict_top_item = {
                    "name_artist": top_item.item.name,
                    "qty_plays": int(top_item.weight),
                }
            elif type_asset == "albums":
                dict_top_item = {
                    "name_artist": top_item.item.artist.name,
                    "name_album": top_item.item.title,
                    "qty_plays": int(top_item.weight),
                }
            elif type_asset == "songs":
                dict_top_item = {
                    "name_artist": top_item.item.artist.name,
                    "name_song": top_item.item.title,
                    "qty_plays": int(top_item.weight),
                }
            lst_results.append(dict_top_item)
        return lst_results

if __name__ == "__main__":
    lstfm = LastFm()
    bio = lstfm.get_artist_bio(name_artist="Nick Cave")
    print(bio)