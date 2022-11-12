import json
import os


class Config:

    _config = None

    def __init__(self, path_to_config):
        self.__load_config(path_to_config)

    def __load_config(self, path_to_config):

        if not os.path.exists(path_to_config):
            raise FileNotFoundError("Config file not found")

        with open(path_to_config, 'r') as f:
            self._config = json.load(f)

        # Parse config and make sure it's valid

    def get(self, key, default=None):
        """Returns the config as a dict"""
        if self._config is None:
            raise ValueError("Config not loaded")
        split_key = key.split('.')
        current = self._config
        for k in split_key:
            if k not in current:
                return default
            current = current[k]
        return current

    def put(self, key, value):
        """Updates the config"""
        if self._config is None:
            raise ValueError("Config not loaded")
        split_key = key.split('.')
        current = self._config
        for k in split_key[:-1]:
            current = current[k]
        current[split_key[-1]] = value
