from fastapi import APIRouter, HTTPException
from dotenv import dotenv_values
import pandas as pd

import os

from lastfm import LastFm
from mpd_client import MPDController

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

lastfm = LastFm(host=config['HOST_CONTROLLER'], port=config['PORT_CONTROLLER'])

router = APIRouter(
    prefix='/lastfm',
    tags=['Last.fm resources']
)

@router.get("/check-credentials/")
async def check_user_credentials():
    if lastfm.check_user_token():
        return{'description': 'All OK!'}
    else:
        raise HTTPException(status_code=401, detail='Let user re-authorize access to Last.fm account')

@router.get("/get-user-access/")
async def open_lastfm_permissions_page():
    result = lastfm.request_user_access(callback_url=f"http://localhost:{config['PORT_CONTROLLER']}/lastfm/receive-token")
    return result

@router.get("/receive-token/")
async def accept_user_token(token: str):
    result = lastfm.save_user_token(token)
    return result

@router.get("/artist/")
async def get_artist_bio(name_artist: str):
    result = lastfm.get_artist_bio(name_artist)
    return result

@router.get("/love/")
async def love_track(name_artist: str, name_song: str):
    lastfm.love_track(name_artist=name_artist, name_song=name_song)
    return { 'details': f"Loved '{name_song}' by {name_artist}"}

@router.get("/albums/top")
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

    return df_mpd.to_dict('records')
