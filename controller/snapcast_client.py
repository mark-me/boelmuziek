import asyncio
import snapcast.control

class SnapServer():
    def __init__(self, host) -> None:
        self.host = host
        self.loop = asyncio.get_event_loop() # Loop needed for snapserver
        self.server = self.loop.run_until_complete(
            snapcast.control.create_server(self.loop, host)
            )

    async def list_clients(self):
       # print all client names
        lst_clients = []
        clients = self.server.clients
        for client in clients:
            lst_clients.append(
                {
                    'friendly_name': client.friendly_name,
                    'identifier': client.identifier,
                    'connected': client.connected,
                    'muted': client.muted,
                    'volume': client.volume,
                    'version': client.version,
                    'name': client.name
                }
            )
        return lst_clients

    async def client_toggle_mute(self, id: str):
        clients = self.server.clients
        for client in clients:
            if(client.identifier == id):
                mute = not client.muted
                client.set_muted(mute)
                return [{
                    'friendly_name': client.friendly_name,
                    'identifier': client.identifier,
                    'muted':client.muted
                         }]

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