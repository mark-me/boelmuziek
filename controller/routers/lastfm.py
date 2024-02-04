from fastapi import APIRouter, HTTPException
from dotenv import dotenv_values

import os

from lastfm import LastFm

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

lastfm = LastFm(host=config['HOST_CONTROLLER'], port=config['PORT_CONTROLLER'])

router = APIRouter(
    prefix='/lastfm',
    tags=['Last.fm resources']
)

@router.get("/check-credentials/")
async def check_user_credentials():
    if lastfm.check_user_token():
        return{'description': 'All OK!'}
    else:
        raise HTTPException(status_code=401, detail='Let user re-authorize access to Last.fm account')

@router.get("/get-user-access/")
async def open_lastfm_permissions_page():
    result = lastfm.request_user_access(callback_url=f"http://localhost:{config['PORT_CONTROLLER']}/lastfm/receive-token")
    return result

@router.get("/receive-token/")
async def accept_user_token(token: str):
    result = lastfm.save_user_token(token)
    return result

@router.get("/artist/")
async def get_artist_info(name_artist: str):
    result = lastfm.get_artist_art(name_artist)
    return result

@router.get("/love/")
async def love_track(name_artist: str, name_song: str):
    lastfm.love_track(name_artist=name_artist, name_song=name_song)
    return { 'details': f"Loved '{name_song}' by {name_artist}"}
