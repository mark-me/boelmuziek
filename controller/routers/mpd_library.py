from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from enum import Enum
from io import BytesIO

from mpd_client import *

mpd = MPDController(host='localhost')

router = APIRouter(
    prefix='/library',
    tags=['MPD library']
)

class TagTypeSearch(str, Enum):
    artist = "artist"
    album = "album"
    song = "song"

@router.get("/artists/")
async def get_artists() -> list:
    lst_results = []
    lst_results = await mpd.get_artists()
    return lst_results

@router.get("/albums/")
async def get_albums(artist_name: str=None):
    lst_results = []
    # All albums if artist name is not supplied
    if(artist_name == None):
        lst_results = await mpd.get_albums()
    else:
        lst_results = await mpd.get_artist_albums(artist_name)
    return lst_results

@router.get("/search/{type}")
async def search_music(type: TagTypeSearch, part_string: str = ...):
    lst_results = []
    lst_results = await mpd.search(type=type.value,
                                   filter=part_string)
    return lst_results

@router.get("/cover/")
async def get_song_cover(file: str):
    dict_image = await mpd.get_cover_art(file)
    headers = {"Content-Type": dict_image['image_format']}
    return StreamingResponse(BytesIO(dict_image['image']), headers=headers)

