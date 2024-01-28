from fastapi import APIRouter
from snapcast_client import *

snapserver = SnapServer(host='localhost')

router = APIRouter(
    prefix='/snapserver',
    tags=['Snapcast server']
)

@router.get("/clients/")
async def list_clients():
    clients = await snapserver.list_clients()
    return clients

@router.get("/client/mute/")
async def mute_client_toggle(id: str):
    result = await snapserver.client_toggle_mute(id)
    return result
