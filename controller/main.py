import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import dotenv_values

from mpd_client import MPDController
from routers import mpd_system, mpd_library, mpd_queue, mpd_playlists, snapserver, discogs, lastfm

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

mpd = MPDController(host=config['HOST_MPD'])

app = FastAPI()
app.include_router(mpd_system.router)
app.include_router(mpd_queue.router)
app.include_router(mpd_library.router)
app.include_router(mpd_playlists.router)
app.include_router(snapserver.router)
app.include_router(lastfm.router)
app.include_router(discogs.router)

@app.get("/", response_class=HTMLResponse)
async def welcome_page(request: Request):
    content = """
    <html>
        <head>
            <title>The controller welcomes you...</title>
        </head>
        <body>
            <h1>The API that dominates MPD </h1>
            <p>You have reached your API to control whatever MPD is doing and asking all about what it knows about your music collection..</p>
            <p>Visit the <a href="/docs">Swagger UI</a> for the API documentation.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5080)