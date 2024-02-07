from dotenv import dotenv_values
from snapcast import control

import asyncio
import os

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

class SnapServer():
    def __init__(self, host) -> None:
        self.host = host
        self.loop = asyncio.get_event_loop() # Loop needed for snapserver
        #self.server = self.loop.run_until_complete(control.create_server(self.loop, self.host))
        self.server = control.create_server(self.loop, self.host)

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
                mute = await client.set_muted(mute)

                return [{
                    'friendly_name': client.friendly_name,
                    'identifier': client.identifier,
                    'muted':client.muted
                         }]

    async def list_groups(self):
        lst_groups = []
        groups = self.server.groups
        for group in groups:
            dict_group = {
                'friendly_name': group.friendly_name,
                'identifier': group.identifier,
                'muted': group.muted,
                'volume': group.volume,
                'stream_status': group.stream_status,
                'name': group.name
                }
            lst_clients = []
            for client in group.clients:
                lst_clients.append({'identifier': client})
            dict_group['clients'] = lst_clients
            lst_groups.append(dict_group)
        return lst_groups

    async def group_mute(self, id_group: str) -> bool:
        await self.server.group_mute(identifier=id_group, status='false')

