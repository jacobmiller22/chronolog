""" Imports """
from api import api
from datetime import datetime
import requests
import binascii
import os
import urllib.parse
import webbrowser
import threading
from killable_thread import KillableThread
import auth_server
from waitress import serve

class GoogleLogApi(api.LogApi):
    
    _GOOGLE_DRIVE_API_URL = "https://www.googleapis.com/drive/v3/files"
    _GOOGLE_DRIVE_API_AUTH_URL = "https://www.googleapis.com/auth/drive.file"
    _GOOGLE_DRIVE_API_SCOPE = "https://www.googleapis.com/auth/drive.file"
    
    _GOOGLE_CHRONOLOG_CLIENT_ID = "445106395721-vgod49ld0oiacrvl4nfkmul4q7hjfmq0.apps.googleusercontent.com"
    _GOOGLE_CHRONOLOG_CLIENT_SECRET = "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"
    _GOOGLE_OAUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    _GOOGLE_TOKEN_ENDPOINT = "https://www.googleapis.com/oauth2/v4/token"
    
    def _create_auth_server(self, state_code, semaphore) -> None:
        serve(auth_server.create_auth_server(state_code=state_code, semaphore=semaphore), host="localhost", port=8080)
    
    def auth(self) -> bool:
        """_summary_

        Returns:
            bool: _description_
        """
        
        # Create a random state
        state = binascii.hexlify(os.urandom(16)).decode('ascii')  
        
        # Serve in a thread, copy the state to a new variable so that the thread can access it
        state_code = (f"{state}", None) # Shared variable, Will be changed by other thread
        state_code_semaphore = threading.Semaphore(0)
        
        thread = KillableThread(None, target=self._create_auth_server, kwargs={"state_code": state_code, "semaphore": state_code_semaphore})
        thread.start()

        # Create OAuth2 request
        oauth2_request = {
            "host": self._GOOGLE_OAUTH_ENDPOINT,
            "params": {
                "response_type": "code",
                "scope": self._GOOGLE_DRIVE_API_SCOPE,
                "client_id": self._GOOGLE_CHRONOLOG_CLIENT_ID,
                "redirect_uri": "http://localhost:8080/google/oauth2/callback",
                "state": state
            }
        }
        oauth2_request_str = oauth2_request["host"] + "?" + urllib.parse.urlencode(oauth2_request["params"])

        # Open the browser for the user to authenticate
        webbrowser.open(oauth2_request_str)
        
        # Acquire the semaphore
        state_code_semaphore.acquire()
        
        # TODO: Check the state code, if successful, end the auth server
        print("STATE CODE CONDITION IS: " + str(state_code))
        thread.kill()
        thread.join()
        
        # Use the code to get the access token
        
        return True   
    
    def find_log_for_grouping(self, date: datetime) -> str:
        """_summary_

        Args:
            date (datetime): _description_

        Returns:
            str: _description_
        """
        group: str = self.find_group(date)
        
        # Try to find the log for the given group
        
        # res = requests.get(self._GOOGLE_DRIVE_API_URL)
        
        # print(res.json())
        
        return "Hello"
    
    def upload_log(self, date: datetime, log_contents: str) -> bool:
        """_summary_

        Args:
            date (datetime): _description_
            log_contents (str): _description_

        Returns:
            bool: _description_
        """
        self.auth()
        self.find_log_for_grouping(date)
        
        return True