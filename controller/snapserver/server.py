from dotenv import dotenv_values
import snapcast.control

import asyncio
import logging
import os

config = {
    **dotenv_values(".env"),  # load shared development variables
    **os.environ,  # override loaded values with environment variables
}

logger = logging.getLogger(__name__)

snapserver_loop = asyncio.get_event_loop()
snapserver = snapserver_loop.run_until_complete(
    snapcast.control.create_server(snapserver_loop, config['HOST_SNAPSERVER'])
    )

class SnapServer():
    def __init__(self, host) -> None:
        self._loop = snapserver_loop
        self.server = snapserver
        self.server.clients[0].set_callback(self.client_status)

    def client_status(self, client):
        logger.info(f"Volume: {client.volume}")

    async def status(self):
        status = self.server.version #await self.server.status()
        return status

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

    async def client_volume(self, id_client: str, volume: int) -> None:
        for client in self.server.clients:
            if(client.identifier == id_client):
                client.update_volume(data={'volume': volume})
        # task_volume = asyncio.create_task(
        #     self.server.client_volume(id_client, {'percent': volume, 'muted': False})
        #     )

    async def client_toggle_mute(self, id_client: str) -> dict:
        for client in self.server.clients:
            if(client.identifier == id_client):
                mute = not client.muted
                task_mute = asyncio.create_task(client.set_muted(mute))

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

    async def group_volume(self, id_group: str, volume: int):
        pass

    async def group_mute(self, id_group: str) -> bool:
        task_mute = asyncio.create_task(
            self.server.group_mute(identifier=id_group, status='false')
        )

