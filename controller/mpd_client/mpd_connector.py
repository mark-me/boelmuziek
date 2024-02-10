import logging

from mpd.asyncio import MPDClient

logging.basicConfig(
    format="%(levelname)s:\t%(asctime)s - %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

class MPDConnection:
    def __init__(self, host, port=6600) -> None:
        self.mpd = MPDClient()
        self.host = host
        self.port = port

    async def connect(self) -> bool:
        """Connects to mpd server.

        :return: Boolean indicating if successfully connected to mpd server.
        """
        if not self.is_connected:
            try:
                logger.info(f"Connecting to MPD server on {self.host}:{self.port}")
                await self.mpd.connect(self.host, self.port)

            except ConnectionError:
                logger.error(
                    f"Failed to connect to MPD server on {self.host}:{self.port}"
                )
                return False
        return True

    @property
    def is_connected(self) -> bool:
        return self.mpd.connected

    @property
    async def command(self):
        await self.connect()
        return self.mpd
