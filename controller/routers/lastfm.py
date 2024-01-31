from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO

from lastfm import LastFm

lastfm = LastFm()

router = APIRouter(
    prefix='/lastfm',
    tags=['Last.fm resources']
)

@router.get("/check-credentials/")
async def check_user_credentials():
    if lastfm.check_user_token():
        return{'description': 'All OK!'}
    else:
        raise HTTPException(status_code=401, description='Let user re-authorize access to Last.fm account')

@router.get("/get-user-access/")
async def open_lastfm_permissions_page():
    result = lastfm.request_user_access()
    return result

@router.get("/receive-token/")
async def accept_user_token(token: str):
    result = lastfm.save_user_token(token)
    return result