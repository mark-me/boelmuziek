from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO

from discogs import Discogs

discogs = Discogs()

router = APIRouter(
    prefix='/discogs',
    tags=['Discogs resources']
)

class Verification(BaseModel):
    code: str

@router.get("/has-credentials/")
async def check_user_credentials():
    result = discogs.has_user_tokens()
    return result

@router.get("/get-user-access/")
async def open_discogs_permissions_page():
    result = discogs.request_user_access()
    return result

@router.post("/supply-verification-code/")
async def validate_verification_code(verification: Verification):
    result = discogs.validate_verification_code(verification.code)
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