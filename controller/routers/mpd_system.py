from fastapi import APIRouter
from dotenv import dotenv_values

import asyncio
import os

from mpd_client.mpd_client import MPDController

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

mpd = MPDController(host=config['HOST_MPD'])

router = APIRouter(
    prefix='/system',
    tags=['MPD status']
)

@router.get("/status/")
async def status():
    """
    Retrieves the server's status on the queue settings, queue progress and playback status
    """
    status = await mpd.get_status()
    return status

@router.get("/output/list")
async def list_outputs():
    """
    Lists the output devices MPD uses to stream it's playback to
    """
    outputs = await mpd.outputs_get()
    return outputs

@router.get("/output/toggle")
async def toggle_output(id_output: int):
    """
    Toggles MPD output streams based on their id.
    """
    outputs = await mpd.output_toggle(id_output)
    return outputs

@router.get('/statistics/')
async def server_statistics():
    """
    Server statistics on uptime, playtime and music library statistics.
    """
    server_stats = await mpd.get_statistics()
    return server_stats

@router.get("/update-db/")
async def update_mpd_library():
    """
    Update the MPD music library to reflect changes to the music files.
    """
    update = await mpd.mpd_client.update()
    return {'details': "Update #" + update}
