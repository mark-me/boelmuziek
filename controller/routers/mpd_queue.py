from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from dotenv import dotenv_values

from io import BytesIO
from pydantic import BaseModel
from enum import Enum
from typing import List
import os

from mpd_client import MPDController

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

mpd = MPDController(host=config['HOST_MPD'])

router = APIRouter(
    prefix='/queue',
    tags=['MPD queue']
)

class QueueControlType(str, Enum):
    play = 'play'
    pause = 'pause'
    stop = 'stop',
    next = 'next'
    previous = 'previous'

class QueueItem(BaseModel):
    file: str

class QueueItems(BaseModel):
    at_position: int
    start_playing: bool = False
    clear_playlist: bool = False
    files: List[QueueItem]

@router.get("/")
async def get_queue():
    queue = await mpd.get_queue()
    return queue

@router.post("/add/")
async def add_to_queue(items: QueueItems):
    position = items.at_position
    first_round = True
    for item in items.files:
        first_round = items.start_playing and first_round
        lst_queue = await mpd.queue_add_file(item.file, position=position, start_playing=first_round)
        position = position + 1
        first_round = False
    return lst_queue

@router.get("/current-song/")
async def get_current_song():
    current_song = await mpd.current_song()
    return current_song

@router.get("/play-time/")
async def seek_position_in_current_song(time_seconds: str):
    await mpd.seek_current_song_time(time_seconds=time_seconds)

@router.get("/play-song/")
async def start_playing_from_queuet(position: int):
    is_success = await mpd.play_on_queue(position=position)
    if is_success:
        msg = {'status_code': 200,
               'details': 'Started playback'}
    else:
        msg = {'status_code': 406,
               'details': 'Unable to start playing'}
    return msg

@router.get("/current-cover/")
async def get_current_song_cover():
    current_song = await mpd.current_song()
    dict_image = await mpd.get_cover_art(current_song['file'])
    headers = {"Content-Type": dict_image['image_format']}
    return StreamingResponse(BytesIO(dict_image['image']), headers=headers)

@router.get("/control/")
async def execute_queue_control(action: QueueControlType):
    await mpd.queue_control_set(action.value)
    control_status = await mpd.get_status()
    return control_status['state']

@router.get("/move/")
async def move_queue_items(start: int, end: int, to: int):
    playlist = await mpd.queue_move(start=start, end=end, to=to)
    return playlist

@router.get("/clear/")
async def clear_queue():
    """Clear the current playlist

    Returns:
        dict: Reports on status of the operation
    """
    await mpd.queue_clear()
    status = await mpd.get_status()
    if status['playlistlength'] == 0:
        return {'status_code': '200', 'detail': 'Cleared playlist'}
    else:
        return {'status_code': 'Error', 'detail': 'Couldn\'t clear playlist'}