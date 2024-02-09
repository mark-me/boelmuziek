from datetime import datetime
import json
import logging
import random
import requests

logger = logging.getLogger(__name__)

class SnapcastRequester:
    def __init__(self, url: str) -> None:
        self.url = url

    def request(self, payload: dict):
        identifier = random.randint(1, 1000)
        payload["id"] = identifier
        payload["jsonrpc"] = "2.0"
        headers = {"content-type": "application/json"}
        response = requests.post(
            self.url, data=json.dumps(payload), headers=headers
        ).json()
        if "result" in response.keys():
            if "params" in payload.keys():
                logger.info(f"Requested method \'{payload['method']}\' with parameters: {payload['params']}")
            else:
                logger.info(f"Requested method \'{payload['method']}\'")
            return response["result"]
        else:
            if "params" in payload.keys():
                logger.info(f"Could not execute method \'{payload['method']}\' with parameters: {payload['params']}")
            else:
                logger.info(f"Could not execute method \'{payload['method']}\'")
            return response["error"]


class SnapcastClient(SnapcastRequester):
    def __init__(self, url: str, data_client: dict) -> None:
        super(SnapcastClient, self).__init__(url=url)
        self._id = data_client["id"]

    @property
    def id_client(self):
        return self._id

    @property
    def _status(self):
        payload = {
            "method": "Client.GetStatus",
            "params": {"id": self._id},
        }
        response = self.request(payload=payload)["client"]
        return response

    @property
    def info(self):
        info = self._status
        info["lastSeen"] = datetime.utcfromtimestamp(
            info["lastSeen"]["sec"]
        ).strftime("%Y-%m-%d %H:%M:%S")
        return info

    @property
    def volume(self):
        volume = self._status["config"]["volume"]["percent"]
        return volume

    @volume.setter
    def volume(self, percent: int):
        payload = {
            "method": "Client.SetVolume",
            "params": {
                "id": self._id,
                "volume": {"muted": False, "percent": percent},
            },
        }
        self.request(payload=payload)

    @property
    def name_client(self) -> str:
        status = self._status
        name = (
            status["host"]["name"]
            if status["config"]["name"] == ""
            else status["config"]["name"]
        )
        return name

    @name_client.setter
    def name_client(self, name: str) -> dict:
        payload = {"method": "Client.SetName", "params": {"id": self._id, "name": name}}
        response = self.request(payload=payload)
        return response


class SnapcastGroup(SnapcastRequester):
    def __init__(self, url: str, data_group: dict) -> None:
        super(SnapcastGroup, self).__init__(url=url)
        self._id = data_group["id"]

    @property
    def id_group(self):
        return self._id

    @property
    def _status(self) -> dict:
        payload = {"method": "Group.GetStatus", "params": {"id": self._id}}
        response = self.request(payload=payload)
        result = response["group"]
        return result

    @property
    def info(self) -> dict:
        status = self._status
        info = {key: status[key] for key in ['id', 'name', 'stream_id']}
        info['volume'] = {
            'muted': status['muted'],
            'percent': self.volume
        }
        lst_clients = []
        for client in self.clients:
            lst_clients.append(client.info)
        info['clients'] = lst_clients
        return info

    @property
    def name_group(self):
        return self._status["name"]

    @name_group.setter
    def name_group(self, name_group: str) -> dict:
        payload = {
            "method": "Group.SetName",
            "params": {"id": self._id, "name": name_group},
        }
        self.request(payload=payload)

    @property
    def clients(self) -> list:
        clients = []
        for dict_client in self._status["clients"]:
            clients.append(SnapcastClient(url=self.url, data_client=dict_client))
        return clients

    @property
    def mute(self) -> bool:
        status = self._status
        mute = status["muted"]
        return mute

    @mute.setter
    def mute(self, value: bool):
        payload = {"method": "Group.SetMute", "params": {"id": self._id, "mute": value}}
        self.request(payload=payload)

    def toggle_mute(self) -> dict:
        mute = not self.mute
        payload = {"method": "Group.SetMute", "params": {"id": self._id, "mute": mute}}
        response = self.request(payload=payload)
        return response

    @property
    def volume(self) -> dict:
        client_volumes = []
        for client in self.clients:
            client_volumes.append(client.volume)
        group_volume = int(sum(client_volumes) / len(client_volumes))
        return group_volume

    @volume.setter
    def volume(self, percent: int):
        group_volume = self.volume
        volume_change = percent - group_volume
        for client in self.clients:
            client_volume = client.volume + volume_change
            client_volume = (
                0
                if client_volume < 0
                else 100
                if client_volume > 100
                else client_volume
            )
            client.volume = client_volume
        self.mute = False


class SnapcastServer(SnapcastRequester):
    def __init__(self, host: str, port: int = 1780):
        url = f"http://{host}:{port}/jsonrpc"
        super(SnapcastServer, self).__init__(url=url)

    def connect(self):
        server = self.status
        self._name = server["server"]["snapserver"]

    @property
    def status(self):
        payload = {"method": "Server.GetStatus"}
        response = self.request(payload=payload)
        status = response["server"]
        return status

    @property
    def groups(self):
        groups = []
        for group in self.status["groups"]:
            groups.append(SnapcastGroup(url=self.url, data_group=group))
        return groups

    def get_groups_info(self):
        lst_groups = []
        for group in self.groups:
            lst_groups.append(group.info)
        return lst_groups
