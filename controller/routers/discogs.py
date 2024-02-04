from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import dotenv_values

from pydantic import BaseModel
from typing import List
from io import BytesIO
import os

from discogs import Discogs

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

discogs = Discogs()

router = APIRouter(
    prefix='/discogs',
    tags=['Discogs resources']
)

class Artist(BaseModel):
    artist: str

@router.get("/check-credentials/")
async def check_user_credentials():
    if discogs.check_user_tokens():
        return{'description': 'All OK!'}
    else:
        raise HTTPException(status_code=401, detail='Let user re-authorize access to Last.fm account')

@router.get("/get-user-access/")
async def open_discogs_permissions_page():
    result = discogs.request_user_access(callback_url=f"http://localhost:{config['PORT_CONTROLLER']}/discogs/receive-token/")
    return result

@router.get("/receive-token/")
async def accept_user_token(oauth_token: str, oauth_verifier: str):
    result = discogs.save_user_token(oauth_verifier)
    return result

@router.get("/artists-image/")
async def get_artists_image(name_artist: str):
    result = discogs.get_artist_image(name_artist)
    if result['status'] == 200:
        headers = {"Content-Type": 'image/jpeg'}
        return StreamingResponse(BytesIO(result['message']), headers=headers)
    else:
        raise HTTPException(status_code=404, detail=f"Artist not found: {name_artist}")
        return result

@router.post("/bulk-artist-images/")
async def import_discogs_artist_images(list_artists: List[Artist]):
    discogs.artist_images_bulk(list_artists)