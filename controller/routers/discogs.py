from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from io import BytesIO

from discogs import Discogs

discogs = Discogs()

router = APIRouter(
    prefix='/discogs',
    tags=['Discogs resources']
)

@router.get("/has-credentials/")
async def check_user_credentials():
    result = discogs.has_user_tokens()
    return result

@router.get("/get-user-access/")
async def open_discogs_permissions_page():
    result = discogs.request_user_access()
    return result

@router.get("/supply-verification-code/")
async def validate_verification_code(verification_code: str):
    result = discogs.validate_verification_code(verification_code)
    return result

@router.get("/artists-image/")
async def get_artists_image(name_artist: str):
    result = discogs.get_artist_image(name_artist)
    if result['status'] == 200:
        headers = {"Content-Type": 'image/jpeg'}
        return StreamingResponse(BytesIO(result['message']), headers=headers)
    else:
        return result