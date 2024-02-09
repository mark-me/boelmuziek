from fastapi import APIRouter, HTTPException
from dotenv import dotenv_values

import os
from pydantic import PositiveInt

from snapserver import SnapcastServer

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
    lst_groups = []
    for group in snapserver.groups:
        lst_groups.append(group.info)
    return lst_groups

@router.get("/group/")
async def get_group_info(id_group: str):
    for group in snapserver.groups:
        if group.id_group == id_group:
            return group.info
    raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

@router.get("/group/volume/")
async def set_group_volume(id_group: str, volume: int):
    """ Set volume on a group of multi-room clients

    - **id_group** - The id of a client
    - **volume** - The volume expressed as a percentage between 0 and 100
    """
    if volume < 0 or volume > 100:
        raise HTTPException(status_code=422,
                            detail="Input should have a value from 0 to 100")
    for group in snapserver.groups:
        if group.id_group == id_group:
            group.volume = volume
            return group.info
    raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

@router.get("/group/mute/")
async def toggle_group_mute(id_group: str):
    """ Mute group of multi-room clients

    - **id_group** - The id of a group of clients
    """
    for group in snapserver.groups:
        if group.id_group == id_group:
            return group.toggle_mute()
    raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

@router.get("/clients/")
async def list_clients(id_group: str):
    """ List multi-room clients
    """
    lst_client_info = []
    for group in snapserver.groups:
        if group.id_group == id_group:
            for client in group.clients:
                lst_client_info.append(client.info)
            return lst_client_info
    raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

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
    for group in snapserver.groups:
        if group.id_group == id_group:
            for client in group.clients:
                client.volume = volume
                return client.info
            raise HTTPException(status_code=404, detail=f"Client {id_client} within group {id_group} not found.")
    raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

@router.get("/client/mute/")
async def toggle_client_mute(id_client: str):
    """ Mute multi-room client

    - **id_group**: The id of a group where the client resides in
    - **id_client**: The id of a client
    """
    for group in snapserver.groups:
        if group.id_group == id_group:
            for client in group.clients:
                client.toggle_mute()
                return client.info
            raise HTTPException(status_code=404, detail=f"Client {id_client} within group {id_group} not found.")
    raise HTTPException(status_code=404, detail=f"Group {id_group} not found.")

