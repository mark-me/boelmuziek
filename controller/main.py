from typing import Union
from enum import Enum
import asyncio
from mpd_client import *
from fastapi import FastAPI
import uvicorn

class TagType(str, Enum):
    artist = "artist"
    album = "album"
    song = "song"

mpd = MPDController(host='localhost')#host='mpd')
#asyncio.run(mpd.connect())
app = FastAPI()

async def connect() -> bool:
    is_connected = mpd.is_connected
    if(not is_connected):
        task_connect = asyncio.create_task(mpd.connect())
        is_connected = await task_connect
    return is_connected

@app.get("/")
async def read_root():
    await connect()
    await mpd.status_get()
    task_control = asyncio.create_task(mpd.player_control_get())
    mpd_control_status = await task_control
    return {"MPD status": mpd_control_status}

@app.get("/artists/")
async def get_artists():
    await connect()
    lst_results = []
    lst_results = await mpd.get_artists()
    return lst_results

@app.get("/albums/")
async def get_artists():
    await connect()
    lst_results = []
    lst_results = await mpd.get_albums()
    return lst_results

@app.get("/search/{type}")
async def search_music(type: TagType, part_string: str):
    await connect()
    lst_results = []
    lst_results = await mpd.search(type=type.value,
                                   filter=part_string)
    return lst_results

@app.get("/playlist/current-song/")
async def current_song():
    await connect()
    current_song = await mpd.current_song()
    return current_song

@app.get("/playlist/")
async def get_current_playlist():
    await connect()
    current_song = await mpd.playlist()
    return current_song

@app.get("/status/")
async def status():
    await connect()
    status = await mpd.get_status()
    return status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5080)