from typing import Union
from enum import Enum
import asyncio
from mpd_client import *
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
import uvicorn
from fastapi.staticfiles import StaticFiles

class TagType(str, Enum):
    artist = "artist"
    album = "album"
    song = "song"

class PlaylistControlType(str, Enum):
    play = 'play'
    pause = 'pause'
    stop = 'stop',
    next = 'next'
    previous = 'previous'

mpd = MPDController(host=host='mpd') #'localhost')
#asyncio.run(mpd.connect())
app = FastAPI()

# Mount a static directory to serve HTML files
app.mount("/static", StaticFiles(directory="controller/static"), name="static")


async def connect() -> bool:
    is_connected = mpd.is_connected
    if(not is_connected):
        task_connect = asyncio.create_task(mpd.connect())
        is_connected = await task_connect
    return is_connected

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    content = """
    <html>
        <head>
            <title>The controller welcomes you</title>
        </head>
        <body>
            <h1>The API that dominates MPD </h1>
            <p>You have reached your API to control whatever MPD is doing and asking all about what it knows about your music collection..</p>
            <p>Visit the <a href="/docs">Swagger UI</a> for the API documentation.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=content)

@app.get("/library/artists/")
async def get_artists():
    await connect()
    lst_results = []
    lst_results = await mpd.get_artists()
    return lst_results

@app.get("/library/albums/")
async def get_artists():
    await connect()
    lst_results = []
    lst_results = await mpd.get_albums()
    return lst_results

@app.get("/library/search/{type}")
async def search_music(type: TagType, part_string: str):
    await connect()
    lst_results = []
    lst_results = await mpd.search(type=type.value,
                                   filter=part_string)
    return lst_results

@app.get("/library/cover/")
async def get_song_cover(file: str, responses = {200: {"content": {"image/png": {}}}}, response_class=Response):
    await connect()
    image_bytes: bytes = await mpd.get_cover_binary(file)
    return Response(content=image_bytes, media_type="image/jpg")

@app.get("/playlist/")
async def get_current_playlist():
    await connect()
    current_song = await mpd.playlist()
    return current_song

@app.get("/playlist/current-song/")
async def get_current_song():
    await connect()
    current_song = await mpd.current_song()
    return current_song

@app.get("/playlist/current-cover/")
async def get_current_song_cover(responses = {200: {"content": {"image/png": {}}}}, response_class=Response):
    await connect()
    current_song = await mpd.current_song()
    image_bytes: bytes = await mpd.get_cover_binary(current_song['file'])
    return Response(content=image_bytes, media_type="image/jpg")

@app.get("/playlist/control/")
async def execute_player_control(action: PlaylistControlType):
    await connect()
    mpd.player_control_set(action)
    task_control = asyncio.create_task(mpd.player_control_get())
    control_status = await task_control
    return control_status

@app.get("/status/")
async def status():
    await connect()
    status = await mpd.get_status()
    return status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5080)