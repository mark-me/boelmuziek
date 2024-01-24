import asyncio
from mpd_client import *

async def main():
    mpd = MPDController(host='localhost')#host='mpd')

    task_connect = asyncio.create_task(mpd.connect())
    is_connected = await task_connect
    if(not mpd.is_connected):
        task_connect = asyncio.create_task(mpd.connect())
        is_connected = await task_connect
    return await mpd.artists_get(part='Che', only_start=False)


asyncio.run(main())