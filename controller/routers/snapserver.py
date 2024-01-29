from fastapi import APIRouter
from snapcast_client import *

snapserver = SnapServer(host='localhost')

router = APIRouter(
    prefix='/snapserver',
    tags=['Snapcast server']
)

@router.get("/groups/")
async def list_groups():
    groups = await snapserver.list_groups()
    return groups

@router.get("/group/mute")
async def mute_group(id_group: str, status: bool):
    snapserver.group_mute(id_group=id_group)

@router.get("/clients/")
async def list_clients():
    clients = await snapserver.list_clients()
    return clients

@router.get("/client/mute/")
async def mute_client_toggle(id: str):
    result = await snapserver.client_toggle_mute(id)
    return result

@router.get("/status/")
async def get_server_status():
    result = snapserver.server.status()
    return result
