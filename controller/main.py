from typing import Union
import asyncio
from mpd_client import *
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    task_connect = asyncio.create_task(mpd.connect())
    is_connected = await task_connect
    return {"MPD connected": is_connected}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
