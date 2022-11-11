""" Imports """
from datetime import datetime
from typing import Union
from api import google




class ChronologApp:
    """ The ChronologApp class is the main class of the Chronolog application. It is responsible for handling the business logic of the application. """
    
    _destinations = ['google_drive']
    _logger = None
    
    def __init__(self, dest: Union[None, str] = None):
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
            # TODO: Read the config file
            raise ValueError(f"Invalid log destination: {dest}")

        
        if not self.is_valid_dest(dest):
            raise ValueError(f"Invalid log destination: {dest}")
        
        if dest == 'google_drive':
            print("Using Google Drive as the log destination")
            self._logger = google.GoogleLogApi()

            

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