import json
import os


class Config:

    _config = None
    _path = None

    def __init__(self, path_to_config):
        self._path = path_to_config
        self.__load_config()

    def __load_config(self):

        if not os.path.exists(self._path):
            raise FileNotFoundError("Config file not found")

        with open(self._path, 'r') as f:
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

        # Save the config
        self.__save()

    def __save(self):
        """ Saves the current config object to the config file """
        with open(self._path, 'w') as f:
            json.dump(self._config, f, indent=2)

    def to_dict(self):
        """Returns the config as a dict"""
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config

    def get_path(self):
        """ Returns the path to the config file """
        return self._path
