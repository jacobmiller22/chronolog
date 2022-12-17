""" Imports """
from datetime import datetime
from typing import Union
from chronolog.api import google
from chronolog.config import Config


class ChronologApp:
    """ The ChronologApp class is the main class of the Chronolog application. It is responsible for handling the business logic of the application. """

    _destinations = ['google_drive']
    _logger = None

    def __init__(self, dest: Union[None, str] = None, path_to_config: Union[None, str] = None):
        if path_to_config is None:
            raise FileNotFoundError("No config file found")
        print(f"Using config file: {path_to_config}")
        self._config = Config(path_to_config=path_to_config)
        self.set_logger(dest)

    def is_valid_dest(self, dest: str):
        """ Checks if the destination is valid """
        return dest in self._destinations

    def set_logger(self, dest: Union[None, str]):
        """
        Instantiates the logger object based on the destination.
        If no destination is provided, chronolog config is used to determine the destination.
        Raises a FileNotFoundError if the config is not found.
        Raises ValueError if the destination is not supported.

        Args:
            logger (str): _description_
        """
        if dest is None:
            dest = self._config.get('destination')

        if not self.is_valid_dest(dest):
            raise ValueError(f"Invalid log destination: {dest}")

        if dest == 'google_drive':
            print("Using Google Drive as the log destination")
            self._logger = google.GoogleLogApi(self._config)

    def upload_log(self, date: datetime, contents: str) -> bool:
        """_summary_

        Raises ValueError is the logger is not set.

        Args:
            date (datetime): _description_
            contents (str): _description_

        Returns:
            bool: _description_
        """
        if self._logger is None:
            raise ValueError("No logger has been set")

        self._logger.upload_log(date, contents)

        return True
