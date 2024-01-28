import asyncio

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
import uvicorn

from mpd_client import *
from routers import mpd_system, mpd_playlist, mpd_library, snapserver

mpd = MPDController(host='localhost') #host='mpd') #

#asyncio.run(mpd.connect())
app = FastAPI()
app.include_router(mpd_system.router)
app.include_router(mpd_playlist.router)
app.include_router(mpd_library.router)
app.include_router(snapserver.router)

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5080)