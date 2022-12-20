import json


class Config:

    _config = None
    _path = None

    def __init__(self, path):
        """Initializes the Config class. Loads the provided config file.

        Args:
            path (str): The path to the config file.

        Raises:
            FileNotFoundError: If the config file is not found.
            ValueError: If the config file is not valid JSON.
        """
        self.__load_config(path)

    def __load_config(self, path):
        try:
            with open(path, "r") as f:
                self._config = json.load(f)
        except FileNotFoundError as file_not_found_error:
            raise FileNotFoundError("Config file not found") from file_not_found_error
        except json.decoder.JSONDecodeError as json_value_error:
            raise ValueError("Config file is not valid JSON") from json_value_error

        self._path = path

    def get(self, key, default=None):
        """Returns the config as a dict"""
        if self._config is None:
            raise ValueError("Config not loaded")
        split_key = key.split(".")
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
        split_key = key.split(".")
        current = self._config
        for k in split_key[:-1]:
            current = current[k]
        current[split_key[-1]] = value

        # Save the config
        self.__save()

    def set_config(self, new_config: dict):
        """Sets the config to the provided config.

        Args:
            new_config (dict): The new config.
        """
        self._config = new_config

        # Save the config
        self.__save()

    def __save(self):
        """Saves the current config object to the config file"""
        with open(self._path, "w") as f:
            json.dump(self._config, f, indent=2)

    def to_dict(self):
        """Returns the config as a dict"""
        if self._config is None:
            raise ValueError("Config not loaded")
        return self._config

    def get_path(self):
        """Returns the path to the config file"""
        return self._path
