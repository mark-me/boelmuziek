from fastapi import APIRouter, HTTPException
from dotenv import dotenv_values

from pydantic import BaseModel
from typing import List
import os

from mpd_client.mpd_client import MPDController

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

mpd = MPDController(host=config['HOST_MPD'])

router = APIRouter(
    prefix='/playlists',
    tags=['MPD playlists']
)


class PlaylistItems(BaseModel):
    name_playlist: str
    files: List[str]


@router.get("/")
async def get_all_playlists():
    """Get the names of all stored playlists"""
    lst_playlists = await mpd.get_playlists()
    return lst_playlists

@router.get("/playlist/")
async def get_playlist(name_playlist: str):
    """Retrieve the songs in a given playlist.

    - **name_playlist**: The name of the stored playlist.
    """
    playlist = await mpd.get_playlist(name_playlist=name_playlist)
    return playlist

@router.post("/add_files/")
async def add_file_to_playlist(items: PlaylistItems):
    """
    Add a list of files to a playlist

    - **name_playlist**: The name of the playlist (new or existing) where the files will be added to
    - **files**: A list of relative MPD filenames to be added to the playlist
    """
    for file in items.files:
        await mpd.playlist_add_file(name_playlist=items.name_playlist, file=file)
    playlist = await mpd.get_playlist(items.name_playlist)
    return playlist

@router.get("/delete-from-playlist/")
async def delete_file_from_playlist(name_playlist: str, position: int):
    """
    Remove a file from a stored playlist by it's index

    - **name_playlist**: The name of the playlist (new or existing) where the files will be added to
    - **position**: The zero-based index of the song in the playlist to be removed
    """
    is_success = await mpd.playlist_delete_song(name_playlist=name_playlist, position=position)
    if is_success:
        playlist = await mpd.get_playlist(name_playlist)
        return playlist
    else:
        raise HTTPException(status_code=406,
                    detail=f"Couldn't remove song at position {position} from playlist '{name_playlist}'")

@router.get("/queue-to-playlist/")
async def save_queue_as_playlist(name_playlist: str):
    """
    Save the playback queue in a new or existing playlist

    - **name_playlist**: The name of the playlist (new or existing) where the files will be added to
    """
    await mpd.queue_to_playlist(name_playlist=name_playlist)
    playlist = await mpd.get_playlist(name_playlist=name_playlist)
    return playlist

@router.get("/enqueue/")
async def add_file_to_playlist(name_playlist: str, start_playing: bool=True):
    """
    Enqueue a playlist to the playback queue

    - **name_playlist**: The name of the playlist (new or existing) from where the files will be added
    - **start_playing**: Indicate whether to start playing the added files immediately or keep playback as is.
    """
    await mpd.playlist_enqueue(name_playlist=name_playlist, start_playing=start_playing)
    play_queue = await mpd.get_queue()
    return play_queue

@router.get("/delete/")
async def remove_playlist(name_playlist: str):
    """
    Delete a stored playlist

    - **name_playlist**: The name of the playlist to be deleted.
    """
    await mpd.playlist_delete(name_playlist=name_playlist)
    lst_playlists = await mpd.get_playlists()
    return lst_playlists

@router.get("/rename/")
async def rename_playlist(name_playlist: str, name_new: str):
    """
    Rename a stored playlist

    - **name_playlist**: The name of the playlist to be deleted.
    - **name_new**: The new name of the playlist.
    """
    await mpd.playlist_rename(name_playlist=name_playlist, name_new=name_new)
    lst_playlists = await mpd.get_playlists()
    return lst_playlists

