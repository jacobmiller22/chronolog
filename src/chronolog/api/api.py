""" Imports """
from datetime import datetime


class LogApiMeta(type):
    """A Parser metaclass that will be used for parser class creation.
    """
    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def __subclasscheck__(cls, subclass):
        _attributes = ["upload_log", "find_log_for_grouping"]
        for attr in _attributes:
            if not hasattr(subclass, attr) or not callable(getattr(subclass, attr)):
                return False
        return True


class LogApi (metaclass=LogApiMeta):
    """_summary_

    Args:
        metaclass (_type_, optional): _description_. Defaults to LogApiMeta.

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """

    _grouping_options = ["daily", "weekly", "monthly", "yearly"]

    def __init__(self, grouping=_grouping_options[0]) -> None:
        self.set_grouping(grouping)

    def get_grouping(self) -> str:
        return self._grouping

    def set_grouping(self, grouping: str) -> None:
        """_summary_

        Args:
            grouping (str): _description_
        """
        if grouping in self._grouping_options:
            self._grouping = grouping
        else:
            raise ValueError("Invalid grouping option")

    def find_group(self, date: datetime) -> str:
        """
        Gets the grouping date for the given date

        Args:
            date (datetime): _description_

        Returns:
            str: _description_
        """
        grouping = self.get_grouping()

        if grouping == "daily":
            return date.strftime("%Y-%m-%d")
        if grouping == "weekly":
            return date.strftime("%Y-%W")
        if grouping == "monthly":
            return date.strftime("%Y-%m")
        if grouping == "yearly":
            return date.strftime("%Y")

        raise ValueError("Invalid grouping option or date")

    def upload_log(self, date: datetime, log_contents: str) -> bool:
        """_summary_

        Args:
            date (datetime): _description_
            log_contents (str): _description_

        Returns:
            bool: _description_
        """
        return True

    def find_log_for_grouping(self, date: datetime) -> str:
        """
        Finda

        Args:
            date (datetime): _description_

        Returns:
            str: _description_
        """
        return "Hello"
