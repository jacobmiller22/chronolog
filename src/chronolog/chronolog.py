""" Imports """
import sys
from datetime import datetime
from typing import Union, Tuple
from chronolog.api import google
from chronolog.config import Config
from chronolog import cli


default_destinations = ["google_drive"]


class ChronologApp:
    """The ChronologApp class is the main class of the Chronolog application. It is responsible for handling the business logic of the application."""

    _destinations = ["google_drive"]
    _logger = None
    _config = None

    # def __init__(self, dest: Union[None, str] = None, path_to_config: Union[None, str] = None):
    #     if path_to_config is None:
    #         raise FileNotFoundError("No config file found")
    #     print(f"Using config file: {path_to_config}")
    #     self._config = Config(path_to_config=path_to_config)
    #     self.set_logger(dest)

    def __init__(self, destinations=None):
        """Initializes the ChronologApp class. If no destinations are provided, the default destinations are used.

        Args:
            destinations (list<string>, optional): The allowed destinations. Defaults to None.
        """

        if destinations is None:
            destinations = default_destinations

        self._destinations = destinations

    def run(self, mode: str = "cli"):
        """Runs the Chronolog application using the provided config file.

        Args:
            mode (str, optional): The mode to run the application in. Defaults to "cli".
        """
        args = None

        if mode == "cli":
            # Run the CLI
            client = cli.Cli()
            args = client.run()

        else:
            raise ValueError(f"Invalid mode: {mode}")

        # Load and validate the config file
        self.__load_config(path=args.get("config_path"))

        # Update the config file if the user requested it
        if args.get("command") == "configure":
            v_success, v_message = self.__validate_config(config=args.get("config"))
            if not v_success:
                print(v_message)
                return
            # Overwrite the config file
            self._config.set_config(new_config=args.get("config"))
            sys.exit(0)

        # Determine if we should exit the application

        # Initialize the logger based on the config file
        self.__set_logger(dest=args.get("destination"))

        # Run the correct function based on the action
        if args.get("command") == "log":
            self.__log(date=args.get("date"), contents=args.get("contents"))

    def __load_config(self, path: str, validate: bool = True):
        """Loads the config file.

        Args:
            path (str): The path to the config file.
        """
        if path is None:
            raise ValueError("No config file provided")

        try:
            self._config = Config(path=path)
        except FileNotFoundError as file_not_found_error:
            print(file_not_found_error)
            return

        if not validate:
            return  # Don't validate the config by exiting the function

        v_success, v_message = self.__validate_config(self._config)
        if not v_success:
            print(v_message)

    def __validate_config(self, config) -> Tuple[bool, str]:
        """Validates the config file.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating if the config is valid, and a string containing the error message.
        """

        if config is None:
            return False, "No config file provided"

        return True, None

    def __set_logger(self, dest: Union[None, str] = None):
        """
        Instantiates the logger object based on the destination.
        If no destination is provided, chronolog config is used to determine the destination.
        Raises a FileNotFoundError if the config is not found.
        Raises ValueError if the destination is not supported.
        """

        if dest is None:
            # Use the default destination from the config file if no destination is provided
            dest = self._config.get("destination")

        if dest not in self._destinations:
            raise ValueError(f"Invalid log destination: {dest}")

        if dest == "google_drive":
            print("Using Google Drive as the log destination")
            try:
                self._logger = google.GoogleLogApi(self._config)
            except ValueError as value_error:
                print("Error occurred while using Google Drive as the log destination: " + str(value_error))
                sys.exit(0)
        else:
            raise ValueError(f"Log destination not implemented: {dest}")

    def __log(self, date: datetime, contents: str):
        """Uploads a log using the previously set logger.

        Args:
            date (datetime): date of the log
            contents (str): contents of the log
        Returns:
            bool: If the log was successfully uploaded
        Raises:
            ValueError is the logger is not set.
        """
        print("Logging...")
        print(self._logger)
        if self._logger is None:
            raise ValueError("No logger has been set")

        self._logger.upload_log(date, contents)
