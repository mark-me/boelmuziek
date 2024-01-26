import asyncio
import snapcast.control

class SnapServer():
    def __init__(self, host) -> None:
        self.host = host
        self.server = None

    async def connect(self):
        self.server = await snapcast.control.create_server(loop=loop, host=self.host)

    async def list_clients(self):
       # print all client names
        return self.server.clients

    async def list_groups(self):
        return self.server.groups


async def main(loop):
    snapserver = SnapServer(host='192.168.0.25')
    await snapserver.connect()
    clients = await snapserver.list_clients()
    for client in clients:
        print(client)
    groups = await snapserver.list_groups()
    for group in groups:
        type(group)
        print(group)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()