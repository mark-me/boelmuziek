from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from io import BytesIO
import asyncio

from pydantic import BaseModel
from enum import Enum
from typing import List

from mpd_client import *

mpd = MPDController(host='localhost')

router = APIRouter(
    prefix='/playlist',
    tags=['MPD playlist']
)

class PlaylistControlType(str, Enum):
    play = 'play'
    pause = 'pause'
    stop = 'stop',
    next = 'next'
    previous = 'previous'

class PlaylistItem(BaseModel):
    file: str

class PlaylistItems(BaseModel):
    at_position: int
    start_playing: bool = False
    clear_playlist: bool = False
    files: List[PlaylistItem]

@router.get("/")
async def get_current_playlist():
    current_playlist = await mpd.playlist()
    return current_playlist

@router.post("/add/")
async def add_to_playlist(items: PlaylistItems):
    position = items.at_position
    first_round = True
    for item in items.files:
        first_round = items.start_playing and first_round
        lst_playlist = await mpd.playlist_add_file(item.file, position=position, start_playing=first_round)
        position = position + 1
        first_round = False
    return lst_playlist

@router.get("/current-song/")
async def get_current_song():
    current_song = await mpd.current_song()
    return current_song

@router.get("/current-cover/")
async def get_current_song_cover():
    current_song = await mpd.current_song()
    dict_image = await mpd.get_cover_art(current_song['file'])
    headers = {"Content-Type": dict_image['image_format']}
    return StreamingResponse(BytesIO(dict_image['image']), headers=headers)

@router.get("/control/")
async def execute_player_control(action: PlaylistControlType):
    await mpd.player_control_set(action.value)
    control_status = await mpd.get_status()
    return control_status['state']

@router.get("/clear/")
async def clear_playlist():
    """Clear the current playlist

    Returns:
        dict: Reports on status of the operation
    """
    await mpd.playlist_clear()
    status = await mpd.get_status()
    if status['playlistlength'] == 0:
        return {'status_code': '200', 'message': 'Cleared playlist'}
    else:
        return{'status': 'Error', 'message': 'Couldn\'t clear playlist'}