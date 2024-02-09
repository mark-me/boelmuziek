from fastapi import APIRouter, HTTPException
from dotenv import dotenv_values

import os
from pydantic import PositiveInt

from snapcast.snapcast import SnapcastServer

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

snapserver = SnapcastServer(host=config['HOST_SNAPSERVER'])

router = APIRouter(
    prefix='/snapserver',
    tags=['Snapcast server']
)

@router.get("/status/")
async def get_server_status():
    """ Status of the multi-room streamer
    """
    status = snapserver.status
    del status['groups']
    return status

@router.get("/groups/")
async def get_info_groups():
    """ List groups of multi-room clients with info
    """
    lst_groups = [group.info for group in snapserver.groups]
    return lst_groups

@router.get("/group/")
async def get_group_info(id_group: str):
    group = next((group for group in snapserver.groups if group.id_group == id_group), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

    return group.info

@router.get("/group/volume/")
async def set_group_volume(id_group: str, volume: int):
    """ Set volume on a group of multi-room clients

    - **id_group** - The id of a client
    - **volume** - The volume expressed as a percentage between 0 and 100
    """
    if volume < 0 or volume > 100:
        raise HTTPException(status_code=422,
                            detail="Input should have a value from 0 to 100")

    group = next((group for group in snapserver.groups if group.id_group == id_group), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

    group.volume = volume

    return group.info

@router.get("/group/mute/")
async def toggle_group_mute(id_group: str):
    """ Mute group of multi-room clients

    - **id_group** - The id of a group of clients
    """
    group = next((group for group in snapserver.groups if group.id_group == id_group), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

    return group.toggle_mute()

@router.get("/clients/")
async def list_clients(id_group: str):
    """ List multi-room clients
    """
    group = next((group for group in snapserver.groups if group.id_group == id_group), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

    lst_info = [client.info for client in group.clients]

    return lst_info

@router.get("/client/volume/")
async def set_client_volume(id_group: str, id_client: str, volume: int):
    """ Set volume on a multi-room client

    - **id_group**: The id of a group where the client resides in
    - **id_client**: The id of a client
    - **volume**: The volume expressed as a percentage between 0 and 100
    """
    if volume < 0 or volume > 100:
        raise HTTPException(status_code=422,
                            detail="Input should have a value from 0 to 100")

    group = next((group for group in snapserver.groups if group.id_group == id_group), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

    client = next((client for client in group.clients if client.id_client == id_client), None)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {id_client} within group {id_group} not found.")

    client.volume = volume
    return client.info


@router.get("/client/mute/")
async def toggle_client_mute(id_group: str, id_client: str):
    """ Mute multi-room client

    - **id_group**: The id of a group where the client resides in
    - **id_client**: The id of a client
    """
    group = next((group for group in snapserver.groups if group.id_group == id_group), None)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

    client = next((client for client in group.clients if client.id_client == id_client), None)
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {id_client} within group {id_group} not found.")

    client.toggle_mute()
    return client.info

