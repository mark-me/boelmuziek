from fastapi import APIRouter
from dotenv import dotenv_values

import os
from pydantic import PositiveInt

from snapserver import SnapServer

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

snapserver = SnapServer(host=config['HOST_SNAPSERVER'])

router = APIRouter(
    prefix='/snapserver',
    tags=['Snapcast server']
)

@router.get("/status/")
async def get_server_status():
    """ Status of the multi-room streamer
    """
    result = await snapserver.status()
    return result

@router.get("/groups/")
async def list_groups():
    """ List groups of multi-room clients
    """
    groups = await snapserver.list_groups()
    return groups

@router.get("/group/volume/")
async def set_group_volume(id_group: str, volume: PositiveInt):
    """ Set volume on a group of multi-room clients

    - **id_group** - The id of a client
    - **volume** - The volume expressed as a percentage between 0 and 100
    """
    snapserver.group_volume(id_group=id_group, volume=volume)

@router.get("/group/mute/")
async def toggle_group_mute(id_group: str):
    """ Mute group of multi-room clients

    - **id_group** - The id of a group of clients
    """
    snapserver.group_mute(id_group=id_group)

@router.get("/clients/")
async def list_clients():
    """ List multi-room clients
    """
    clients = await snapserver.list_clients()
    return clients

@router.get("/client/volume/")
async def set_client_volume(id_client: str, volume: PositiveInt):
    """ Set volume on a multi-room client

    - **id_client** - The id of a client
    - **volume** - The volume expressed as a percentage between 0 and 100
    """
    await snapserver.client_volume(id_client=id_client, volume=volume)

@router.get("/client/mute/")
async def toggle_client_mute(id_client: str):
    """ Mute multi-room client

    - **id_client** - The id of a group of clients
    """
    result = await snapserver.client_toggle_mute(id_client)
    return result

