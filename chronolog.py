""" Imports """
from datetime import datetime
from api import google


def upload_log(date: datetime, contents: str) -> bool:
    """_summary_

    Args:
        date (datetime): _description_
        contents (str): _description_

    Returns:
        bool: _description_
    """
    
    logger = google.GoogleLogApi()
    logger.upload_log(date, contents)
    print("Hello")
    
    return True