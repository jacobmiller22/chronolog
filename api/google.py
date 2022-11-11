""" Imports """
from datetime import datetime
import os
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from api import api
import json

class GoogleLogApi(api.LogApi):
    
    _GOOGLE_DRIVE_API_URL = "https://www.googleapis.com/drive/v3/files"
    _GOOGLE_DRIVE_API_AUTH_URL = "https://www.googleapis.com/auth/drive.file"
    
    
    _GOOGLE_CHRONOLOG_CLIENT_ID = "445106395721-vgod49ld0oiacrvl4nfkmul4q7hjfmq0.apps.googleusercontent.com"
    _GOOGLE_CHRONOLOG_CLIENT_SECRET = "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"
    _GOOGLE_OAUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    _GOOGLE_TOKEN_ENDPOINT = "https://www.googleapis.com/oauth2/v4/token"
    
    _GOOGLE_CLIENT_SECRETS_FILE = "google_credentials.json"
    _GOOGLE_DRIVE_API_SCOPE = "https://www.googleapis.com/auth/drive.file"
    
    _credentials = None
    
    def __init__(self) -> None:
        if not self.auth():
            raise Exception("Could not authenticate with Google Drive")
        super().__init__()

    
    
    def _auth(self) -> bool:
        """
        Helper function to authenticate with Google Drive, will authenticate regardless whether or not the user has already authenticated

        Returns:
            bool: whether or not the authentication was successful
        """
        client_secrets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "credentials", self._GOOGLE_CLIENT_SECRETS_FILE))
        flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes=[self._GOOGLE_DRIVE_API_SCOPE])
        
        credentials = flow.run_local_server(
            host='localhost',port=8080, 
            authorization_prompt_message='Please visit this URL: {url}', 
            success_message='The auth flow is complete; you may close this window.',
            open_browser=True)
            
        # Give the credentials object to the GoogleLogApi class
        self._credentials = credentials
        
        return self._credentials is not None 
        
    def auth(self) -> bool:
        """
        Authenticates the user with Google in the required scopes. If the user has already authenticated, this will not prompt the user to authenticate again.

        Returns:
            bool: whether or not the authentication was successful
        """
        
        # Get the credentials from the file
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', [self._GOOGLE_DRIVE_API_SCOPE])

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._credentials = creds
            else:
                self._auth() # Stores the credentials in the class
            # Save the credentials for the next run
            if self._credentials is not None:
                with open('token.json', 'w', encoding="utf8") as token:
                    token.write(self._credentials.to_json())
        # Otherwise, give the credentials object to the GoogleLogApi class
        else:
            self._credentials = creds
        
        # Success if the credentials are not None
        return self._credentials is not None
    
    def _build_batch_requests(self, title: str, date: str, contents: str, doc: dict):
        """
        Creates a new batch requets list for the Google Drive API

        Args:
            title (str): The title of the document
            date (str) The date to log
            contents (str): The contents of the log
            doc (dict): the current document specification
        """
        # TODO: Add a title field to the document
        
        # Check if the document has an entry for this date
        date_exists = doc['body']['content'][1]['paragraph']['elements'][0]['textRun']['content'].find(date) != -1
        
        # If the date exists, then we need to update the contents and not create a new heading
        insertions = []
        if date_exists:
            insertions = [
                {
                    "insertText": {
                        "text": '\n' + contents,
                        "location": {
                            "index": len(date) + len(doc['body']['content'][2]['paragraph']['elements'][0]['textRun']['content']) + 1
                        }
                    }
                },
            ]
        else:
            insertions = [
                {
                    "insertText": {
                        "text": date + '\n',
                        "location": {
                            "index": 1
                        }
                    }
                },
                {
                    "insertText": {
                        "text": contents + '\n',
                        "location": {
                            "index": len(date) + 2
                        }
                    }
                },
            ]
        
        return [
            *insertions,
            {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": len(date) + 1
                    },
                    "paragraphStyle": {
                        "namedStyleType": "HEADING_1",
                    },
                    "fields": "namedStyleType"
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": len(date) + 2,
                        "endIndex": len(date) + len(contents) + 2
                    },
                    "paragraphStyle": {
                        "namedStyleType": "NORMAL_TEXT",
                    },
                    "fields": "namedStyleType"
                }
            },
        ]
    
    
    def upload_log(self, date: datetime, log_contents: str) -> bool:
        """_summary_

        Args:
            date (datetime): _description_
            log_contents (str): _description_

        Returns:
            bool: _description_
        """

        group: str = self.find_group(date)
        
        print("Searching drive for log for group: " + group)
        # Try to find the log for the given group
        with build('drive', 'v3', credentials=self._credentials) as ds:
            target_log_id = None
            next_page_token = None
            while True:
                results = ds.files().list(q=f"name='{group}' and mimeType='application/vnd.google-apps.document'", pageToken=next_page_token).execute()
                items = results.get('files', [])
                for item in items:
                    # If the log is found, store the id
                    if item['name'] == group:
                        target_log_id = item['id']
                        break
                # If there is not another page of results, break
                if results.get('nextPageToken') is None:
                    break
                # Set the next page token
                next_page_token = results.get('nextPageToken')
                    
                print(results)
        
        with build("docs", "v1", credentials=self._credentials) as docs:
            if target_log_id is None:
                print("Log not found, creating new log...")
                target_log_id = docs.documents().create(body={"title": group}).execute()['documentId'] # Creates a blank document with the title of the group, and stores the id

            # Update the log with the new contents
            
            if target_log_id is None:
                print("Failed to create new log")

            
            # Get the current contents of the log
            log = docs.documents().get(documentId=target_log_id).execute()

            # Update the log
            docs.documents().batchUpdate(documentId=target_log_id, body={
                "requests": self._build_batch_requests(title=group, date=date.strftime("%m/%d/%Y"), contents=log_contents, doc=log)
            }).execute()
        
        return True