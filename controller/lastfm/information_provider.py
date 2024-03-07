import json
import logging

from dateutil import parser
from lastfmxpy import (
    methods,
    params,
)
import pandas as pd

from lastfm_client import LastFmClient

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class LastFmInfo(LastFmClient):
    def __init__(self) -> None:
        super(LastFmInfo, self).__init__()

    def get_artist_bio(self, name_artist: str) -> str:
        response: str = self._client.post(
            method=methods.Artist.GET_INFO,
            params=params.ArtistGetInfo(artist=name_artist),
            additional_params=dict(format="json"),
        )
        artist = json.loads(response)["artist"]
        return artist["bio"]["content"]

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

    def get_loved_tracks(self, page: int = 1) -> list:
        logger.info(f"Get {self._username}'s loved tracks")
        result = self._client.post(
            method=methods.User.GET_LOVED_TRACKS,
            params=params.UserGetLovedTracks(
                user=self._username, page=page, api_key=self._api_key
            ),
            additional_params=dict(format="json"),
        )
        lst_tracks = json.loads(result)["lovedtracks"]["track"]
        lst_loved_tracks = []
        for track in lst_tracks:
            lst_loved_tracks.append(
                {
                    "datetime": parser.parse(track["date"]["#text"]),
                    "timestamp": int(track["date"]["uts"]),
                    "name_song": track["name"],
                    "name_artist": track["artist"]["name"],
                }
            )
        return lst_loved_tracks

    def get_recent_songs(self, time_to: str, time_from: str = 0, page: int = 1):
        lst_songs = []
        response: str = self._client.post(
            method=methods.User.GET_RECENT_TRACKS,
            params=params.UserGetRecentTracks(
                user=self._username,
                page=page,
                extended=True,
                to=time_to,
                from_=time_from,
                limit=1000,
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
                    "name_album": recent_song["album"]["#text"],
                    "dt_played": parser.parse(recent_song["date"]["#text"]),
                }
            )
        return lst_songs
