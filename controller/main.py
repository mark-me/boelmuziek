from typing import Union
import asyncio
from mpd_client import *
from fastapi import FastAPI
import uvicorn

mpd = MPDController(host='localhost')#host='mpd')
#asyncio.run(mpd.connect())
app = FastAPI()

@app.get("/")
async def read_root():
    task_connect = asyncio.create_task(mpd.connect())
    is_connected = await task_connect
    await mpd.status_get()
    task_control = asyncio.create_task(mpd.player_control_get())
    mpd_control_status = await task_control
    return {"MPD status": mpd_control_status}

@app.get("/search/{type}/{part_string}")
async def read_artists(type: str, part_string: str):
    if(not mpd.is_connected):
        task_connect = asyncio.create_task(mpd.connect())
        is_connected = await task_connect
    lst_results = []
    if(type=='artist'):
        lst_results = await mpd.artists_get(part=part_string, only_start=False)
    elif(type=='album'):
        lst_results = await mpd.albums_get(part=part_string, only_start=False)
    elif(type=='title'):
        lst_results = await mpd.songs_get(part=part_string, only_start=False)
    return lst_results

@app.get("/lookfor/{type}/{part_string}")
async def search_music(type: str, part_string: str):
    if(not mpd.is_connected):
        task_connect = asyncio.create_task(mpd.connect())
        is_connected = await task_connect
    lst_results = []
    lst_results = await mpd.search(type=type,
                                   filter=part_string)
    return lst_results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5080)