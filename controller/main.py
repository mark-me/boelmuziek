from enum import Enum
from io import BytesIO
import asyncio
from mpd_client import *
from snapcast_client import *
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel
import uvicorn

class TagTypeSearch(str, Enum):
    artist = "artist"
    album = "album"
    song = "song"

class TagTypeControl(str, Enum):
    artist = "artist"
    album = "album"
    file = "file"

class PlaylistControlType(str, Enum):
    play = 'play'
    pause = 'pause'
    stop = 'stop',
    next = 'next'
    previous = 'previous'

class PlaylistItem(BaseModel):
    file: str
    position: int
    start_playing: bool


mpd = MPDController(host='localhost') #host='mpd') #
snapserver = SnapServer(host='localhost')
#asyncio.run(mpd.connect())
app = FastAPI()


async def mpd_connect() -> bool:
    is_connected = mpd.is_connected
    if(not is_connected):
        task_connect = asyncio.create_task(mpd.connect())
        is_connected = await task_connect
    return is_connected

# Function to determine image format (PNG or JPG) based on magic bytes
def determine_image_format(image_data: bytes) -> str:
    if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return "image/png"
    elif image_data.startswith(b'\xff\xd8'):
        return "image/jpeg"
    else:
        raise ValueError("Unsupported image format")

@app.get("/", response_class=HTMLResponse)
async def welcome_page(request: Request):
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
    await mpd_connect()
    lst_results = []
    lst_results = await mpd.get_artists()
    return lst_results

@app.get("/library/albums/")
async def get_albums(artist_name: str | None = None):
    await mpd_connect()
    lst_results = []


    # All albums if artist name is not supplied
    if(artist_name == None):
        lst_results = await mpd.get_albums()
    else:
        lst_results = await mpd.get_artist_albums(artist_name)

    return lst_results

@app.get("/library/search/{type}")
async def search_music(type: TagTypeSearch, part_string: str = ...):
    await mpd_connect()
    lst_results = []
    lst_results = await mpd.search(type=type.value,
                                   filter=part_string)
    return lst_results

@app.get("/library/cover/")
async def get_song_cover(file: str):
    await mpd_connect()
    image_bytes: bytes = await mpd.get_cover_binary(file)
    image_format = determine_image_format(image_bytes)
    headers = {"Content-Type": image_format}
    return StreamingResponse(BytesIO(image_bytes), headers=headers)

@app.get("/playlist/")
async def get_current_playlist():
    await mpd_connect()
    current_song = await mpd.playlist()
    return current_song

@app.get("/playlist/add/{type}")
async def add_to_playlist(type: TagTypeControl, name: str):
    await mpd_connect()
    added_songs = await mpd.playlist_add(type_asset=type.value,
                                         name=name)
    return added_songs

@app.get("/playlist/current-song/")
async def get_current_song():
    await mpd_connect()
    current_song = await mpd.current_song()
    return current_song

@app.get("/playlist/current-cover/")
async def get_current_song_cover():
    await mpd_connect()
    current_song = await mpd.current_song()
    image_bytes: bytes = await mpd.get_cover_binary(current_song['file'])
    image_format = determine_image_format(image_bytes)
    headers = {"Content-Type": image_format}
    return StreamingResponse(BytesIO(image_bytes), headers=headers)

@app.get("/playlist/control/")
async def execute_player_control(action: PlaylistControlType):
    await mpd_connect()
    mpd.player_control_set(action)
    task_control = asyncio.create_task(mpd.player_control_get())
    control_status = await task_control
    return control_status

@app.get("/playlist/clear/")
async def clear_playlist():
    await mpd_connect()
    await mpd.playlist_clear()
    status = await mpd.get_status()
    if status['playlistlength'] == 0:
        return {'status': 'OK', 'message': 'Cleared playlist'}
    else:
        return{'status': 'Error', 'message': 'Couldn\'t clear playlist'}

@app.get("/status/")
async def status():
    await mpd_connect()
    status = await mpd.get_status()
    return status

@app.get("/output/list")
async def list_outputs():
    await mpd_connect()
    outputs = await mpd.outputs_get()
    return outputs

@app.get("/output/toggle")
async def toggle_output(id_output: int):
    await mpd_connect()
    outputs = await mpd.output_toggle(id_output)
    return outputs

@app.get("/snapsever/clients")
async def list_clients():
    clients = await snapserver.list_clients()
    return clients

@app.get("/snapsever/client/mute/")
async def mute_client_toggle(id: str):
    result = await snapserver.client_toggle_mute(id)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5080)