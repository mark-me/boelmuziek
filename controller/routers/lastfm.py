from fastapi import APIRouter, BackgroundTasks, HTTPException
from dotenv import dotenv_values
import pandas as pd

from enum import Enum
import os

from lastfm import LastFm

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

lastfm = LastFm(host=config['HOST_CONTROLLER'], port=config['PORT_CONTROLLER'])

router = APIRouter(
    prefix='/lastfm',
    tags=['Last.fm resources']
)

class TypeAsset(str, Enum):
    artist = "artists"
    album = "albums"
    song = "songs"

@router.get("/check-credentials/")
async def check_user_credentials():
    """ Check if the user already has given the app access to Last.fm
    """
    if lastfm.check_user_data():
        return{'description': 'All OK!'}
    else:
        raise HTTPException(status_code=401, detail='Let user (re-)authorize access to her/his Last.fm account')

@router.get("/get-user-access/")
async def open_lastfm_permissions_page(username: str, background_tasks: BackgroundTasks):
    """ Launching the Last.fm webpage to request access. Once granted the callback url is used for verification.

    - **username**, not strictly necessary for the authorization process, but aids user statistics retrieval
    """
    result = lastfm.request_user_access(username=username)
    background_tasks.add_task(wait_authorization, result['url'])
    return result

def wait_authorization(url: str):
    lastfm.await_authorization(url)

@router.get("/artist/")
async def get_artist_bio(name_artist: str):
    """ Retrieving the artist bio

    - **name_artist** - The artist's name (surprise, surprise)
    """
    result = lastfm.get_artist_bio(name_artist)
    if result is None:
        raise HTTPException(status_code=401,detail="App not authorized for last.fm or invalid user token")
    return result

@router.get("/love-song/")
async def love_track(name_artist: str, name_song: str):
    """ Setting 'loved' for a song on Last.fm

    - **name_artist**: Name of artist
    - **name_song**: Name of the song to set to 'loved'
    """
    is_success = lastfm.love_track(name_artist=name_artist, name_song=name_song)
    if is_success:
        return { 'details': f"Loved '{name_song}' by {name_artist}"}
    else:
        HTTPException(500, "Either network or authorization issue")

@router.get("/loved/")
async def get_loved_songs(limit: int=1000):
    """  Retrieving loved songs

    - **limit**: The number of assets you want to retrieve, max = 1000
    """
    lst_songs = lastfm.get_loved_tracks(limit=limit)
    return lst_songs

@router.get("/top-assets/")
async def get_top_assets(type_asset: TypeAsset, limit: int=1000):
    """ Retrieving top scrobbled media assets on Last.fm

    - **type_asset**: Type of assets you want to aggregate your scrobbles to
    - **limit**: The number of assets you want to retrieve, max = 1000
    """
    lst_results = lastfm.get_top_assets(type_asset=type_asset.value,
                                        limit=limit)
    return lst_results

""" @router.get("/albums/top")
async def get_most_played_albums():
    lastfm_albums = lastfm.get_top_albums()
    df_lastfm = pd.DataFrame(lastfm_albums)
    df_lastfm['name_artist'] = df_lastfm['name_artist'].str.lower()
    df_lastfm['name_album'] = df_lastfm['name_album'].str.lower()
    df_lastfm.to_csv('temp.csv')

    mpd = MPDController(host=config['HOST_MPD'])
    mpd_albums = await mpd.get_albums()
    df_mpd = pd.DataFrame(mpd_albums)
    df_mpd.columns = ['name_artist', 'name_album']
    df_mpd['name_artist_lower'] = df_mpd['name_artist'].str.lower()
    df_mpd['name_album_lower'] = df_mpd['name_album'].str.lower()

    df_mpd = pd.merge(left=df_mpd,
                       right=df_lastfm,
                       how="inner",
                       left_on=['name_artist_lower', 'name_album_lower'],
                       right_on=['name_artist', 'name_album'])
    df_mpd = df_mpd.drop(['name_artist_lower', 'name_album_lower', 'name_artist_y', 'name_album_y'], axis=1).fillna(0)
    df_mpd.columns = ['name_artist', 'name_album', 'qty_plays']
    df_mpd['qty_plays'] = df_mpd['qty_plays'].str

    return df_mpd.to_dict('records') """

