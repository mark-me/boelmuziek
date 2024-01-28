from fastapi import APIRouter
import asyncio
from mpd_client import *

mpd = MPDController(host='localhost')

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

@router.get("/output/toggle")
async def toggle_output(id_output: int):
    await mpd_connect()
    outputs = await mpd.output_toggle(id_output)
    return outputs