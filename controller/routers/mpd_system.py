from fastapi import APIRouter
from dotenv import dotenv_values

import asyncio
import os

from mpd_client import MPDController

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

mpd = MPDController(host=config['HOST_MPD'])

async def mpd_connect() -> bool:
    is_connected = mpd.is_connected
    if(not is_connected):
        task_connect = asyncio.create_task(mpd.connect())
        is_connected = await task_connect
    return is_connected

router = APIRouter(
    prefix='/system',
    tags=['MPD status']
)

@router.get("/status/")
async def status():
    await mpd_connect()
    status = await mpd.get_status()
    return status

@router.get("/output/list")
async def list_outputs():
    await mpd_connect()
    outputs = await mpd.outputs_get()
    return outputs

@router.get('/statistics/')
async def server_statistics():
    await mpd_connect()
    server_stats = await mpd.get_statistics()
    return server_stats

@router.get("/output/toggle")
async def toggle_output(id_output: int):
    await mpd_connect()
    outputs = await mpd.output_toggle(id_output)
    return outputs

@router.get("/update-db/")
async def update_mpd_library():
    await mpd_connect()
    update = await mpd.mpd_client.update()
    return {'message': "Update #" + update}