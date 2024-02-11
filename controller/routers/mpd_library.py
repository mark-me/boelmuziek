from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from dotenv import dotenv_values
from enum import Enum
from io import BytesIO
import os

from mpd_client.mpd_library import MPDLibrary

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

library = MPDLibrary(host=config["HOST_MPD"])

router = APIRouter(prefix="/library", tags=["MPD library"])


class TagTypeSearch(str, Enum):
    artist = "artist"
    album = "album"
    song = "song"


@router.get("/artists/")
async def get_artists() -> list:
    """Get a list of all the artists"""
    lst_results = await library.get_artists()
    return lst_results


@router.get("/artists/random/")
async def get_artists_random(qty_artists: int = 15):
    if qty_artists < 1:
        HTTPException(
            status_code=401, detail="At least one artist must be randomly picked"
        )
    result = await library.get_artists_random(qty_artists=qty_artists)
    return result


@router.get("/albums/")
async def get_albums(artist_name: str = None) -> list:
    """Get a list of albums

    - **artist_name**: Get albums of an artist or if nothing is passed all albums are retrieved.
    """
    lst_results = []
    # All albums if artist name is not supplied
    if artist_name is None:
        lst_results = await library.get_albums()
    else:
        lst_results = await library.get_artist_albums(artist_name)
    return lst_results


@router.get("/albums/random/")
async def get_albums_random(qty_albums: int = 15):
    if qty_albums < 1:
        HTTPException(
            status_code=401, detail="At least one album must be randomly picked"
        )
    result = await library.get_albums_random(qty_albums=qty_albums)
    return result


@router.get("/album/")
async def get_album(name_artist: str, name_album: str) -> dict:
    result = await library.get_album(name_artist=name_artist, name_album=name_album)
    return result


@router.get("/artist-albums/")
async def get_album(name_artist: str):
    """Get a list a specific album

    - **artist_name**: Get albums of an artist or if nothing is passed all albums are retrieved.
    """
    lst_results = []
    # All albums if artist name is not supplied
    lst_results = await library.get_artist_albums(name_artist=name_artist)
    return lst_results


@router.get("/song/")
async def get_song_versions(
    name_song: str, name_artist: str = None, is_cover: bool = False
):
    lst_results = []
    lst_results = await library.get_song(
        name_artist=name_artist, name_song=name_song, is_cover=is_cover
    )
    return lst_results


@router.get("/search/{type}")
async def search_music(
    type: TagTypeSearch, search_string: str, starts_with: bool = None
):
    """Searching for artists, albums or songs

    - **type**: The type assets you're looking for
    - **search_string**: Part of the string you want to look for. The search is case-insensitive.
    """
    lst_results = []
    lst_results = await library.search(
        type=type.value, filter=search_string, starts_with=starts_with
    )
    return lst_results


@router.get("/cover-song/")
async def get_song_cover(file: str):
    """Retrieve the cover-art of a MPD file

    - **file**: The MPD file you want to retrieve the cover-art for
    """
    dict_image = await library.get_cover_art(file)
    headers = {"Content-Type": dict_image["image_format"]}
    return StreamingResponse(BytesIO(dict_image["image"]), headers=headers)


@router.get("/cover-album/")
async def get_album_cover(name_album_artist: str, name_album: str):
    """Retrieve the cover-art of a MPD file

    - **name_album_artist**: The album artist (if the album contains several artists, this is likely 'Various Artists')
    - **name_album**: Name of the album you're looking for.
    """
    dict_image = await library.get_album_cover(
        name_artist=name_album_artist, name_album=name_album
    )
    if dict_image is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cover art not found for '{name_album_artist} - {name_album}'",
        )
    headers = {"Content-Type": dict_image["image_format"]}
    return StreamingResponse(BytesIO(dict_image["image"]), headers=headers)
