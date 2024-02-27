import yaml
import os

class SecretsYAML():
    def __init__(self, file_path: str, app: str, expected_keys: set) -> None:
        self._file = file_path
        self.__create_path()

        self._app = app
        self._expected_keys = expected_keys

    def __create_path(self) -> None:
        path = os.path.dirname(self._file)
        isExist = os.path.isdir(path)
        if not isExist:   # Create a new directory because it does not exist
            os.makedirs(path)

    def is_complete(self):
        """See is all expected fields are present in the secrets file

        Returns:
            dict: A status code and description of the test
        """
        # Check file existence
        if not os.path.isfile(self._file):
            return False, 'There is no config file for secrets in ' + self._file
        # Load the YAML file
        with open(self._file, 'r') as file:
            try:
                yaml_data = yaml.safe_load(file)
            except yaml.YAMLError as e:
                return {'status_code': 500,
                        'detail': f"Error loading file: {str(e)}"}

        # Check if there are any app settings
        if self._app not in yaml_data.keys():
            return False, f"No settings for {self._app} in : {self._file}"

        # Check if there are apps
        missing_keys = self._expected_keys - set(yaml_data[self._app].keys())
        if missing_keys:
            return False, f"Missing keys {', '.join(missing_keys)} for {self._app} in file {self._file}"

        return True, 'YAML file is valid'

    def write_secrets(self, dict_secrets: dict) -> None:
        """Write a secrets on an app to a YAML file

        Args:
            dict_secrets (dict): dictionary containing the secrets
        """
        try:
            with open(self._file, 'r') as file:
                yaml_data = yaml.safe_load(file)
        except IOError:
            yaml_data = {}
            with open(self._file, 'w') as file:
                pass
        yaml_data[self._app] = dict_secrets
        with open(self._file, 'w') as file:
            yaml.safe_dump(yaml_data, file)

    def read_secrets(self) -> dict:
        """Read an app's secrets

        Returns:
            dict: All secrets
        """
        is_complete, value = self.is_complete()
        if is_complete:
            with open(self._file, 'r') as file:
                yaml_data = yaml.safe_load(file)
            return yaml_data[self._app]
        else:
            return None
