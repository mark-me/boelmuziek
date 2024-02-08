from datetime import datetime
import json
import random
import requests

class SnapcastRequester:
    def __init__(self, url: str) -> None:
        self.url = url

    def request(self, payload: dict):
        identifier = random.randint(1, 1000)
        payload['id'] = identifier
        payload['jsonrpc'] ='2.0'
        headers = {'content-type': 'application/json'}
        response = requests.post(
            self.url, data=json.dumps(payload), headers=headers
        ).json()
        return response['result']


class SnapcastClient(SnapcastRequester):
    def __init__(self, url: str, data_client: dict) -> None:
        super(SnapcastClient, self).__init__(url=url)
        self._id = data_client['id']

    @property
    def id_client(self):
        return self._id

    def status(self):
        payload = {
            'method': 'Client.GetStatus',
            'params': {'id': self._id},
        }
        response = self.request(payload=payload)
        result = response['client']
        result['lastSeen']['sec'] = datetime.utcfromtimestamp(result['lastSeen']['sec']).strftime('%Y-%m-%d %H:%M:%S')
        return response['client']

    def get_volume(self):
        status = self.status()
        volume = status['config']['volume']
        return volume

    def set_volume(self, perc_volume: int):
        payload = {
            'method': 'Client.SetVolume',
            'params': {
                'id': self._id,
                'volume': {'muted': False,
                           'percent': perc_volume},
            },
        }
        return self.request(payload=payload)

    def set_name(self, name: str) -> dict:
        payload = {
            'method': 'Client.SetName',
            'params': {'id': self._id,
                       'name': name}
        }
        response = self.request(payload=payload)
        return response


class SnapcastGroup(SnapcastRequester):
    def __init__(self, url: str, data_group: dict) -> None:
        super(SnapcastGroup, self).__init__(url=url)
        self._id = data_group['id']
        self.clients = {}
        for dict_client in data_group['clients']:
            self.clients[dict_client['id']] = SnapcastClient(url=self.url, data_client=dict_client)

    @property
    def id_group(self):
        return self._id

    def get_client_ids(self):
        lst_clients = list(self.clients.keys())
        return lst_clients

    def get_status(self) -> dict:
        payload = {
            'method': 'Group.GetStatus',
            'params':{'id': self._id}
        }
        response = self.__request(payload=payload)
        result = response['group']
        return result

    def get_mute(self) -> bool:
        status = self.get_status()
        mute = status['config']['volume']['muted']
        return mute

    def set_name(self, name: str) -> dict:
        payload = {
            'method': 'Group.SetName',
            'params': {'id': self._id,
                       'name': name}
        }
        response = self.__request(payload=payload)
        return response

    def toggle_mute(self) -> dict:
        mute = not self.get_mute()
        payload = {
            'method': 'Group.SetMute',
            'params': {'id': self._id,
                       'mute': mute}
        }
        response = self.__request(payload=payload)
        return response


class SnapcastServer(SnapcastRequester):
    def __init__(self, host: str, port: int = 1780):
        url = f"http://{host}:{port}/jsonrpc"
        super(SnapcastServer, self).__init__(url=url)
        self._headers = {'content-type': 'application/json'}
        self.clients: list = None

    def status(self):
        payload = {'method': 'Server.GetStatus'}
        response = self.request(payload=payload)
        status = response['server']
        return status

    def initialize(self):
        server = self.status()
        self._name = server['server']['snapserver']
        self.groups = {}
        for group in server['groups']:
            self.groups[group['id']] = SnapcastGroup(url= self.url, data_group=group)

    def get_group_ids(self):
        lst_groups = list(self.groups.keys())
        return lst_groups

    def get_groups(self):
        lst_groups = list(self.groups.values())
        lst_status = []
        for group in lst_groups:
            lst_status.append(group.get_status())
        return lst_status

    def get_client_ids(self):
        lst_clients = []
        lst_groups = self.get_group_ids()
        for id_group in lst_groups:
            group = self.groups[id_group]
            group_clients = group.get_client_ids()
            lst_clients = lst_clients + group_clients
        return lst_clients


def main():
    snapserver = SnapcastServer(host='localhost') #"192.168.0.25") #
    snapserver.initialize()
    print(snapserver.get_group_ids())
    print(snapserver.get_client_ids())
    #print(snapserver.get_groups())

if __name__ == "__main__":
    main()
