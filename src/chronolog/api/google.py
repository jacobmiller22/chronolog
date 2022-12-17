""" Imports """
from datetime import datetime
import os
from typing import Union
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from chronolog.api import api
from chronolog.config import Config
from chronolog.definitions import ROOT_DIR, GOOGLE_CLIENT_SECRETS_FILE, GOOGLE_DRIVE_API_SCOPES


class GoogleLogApi(api.LogApi):
    """ The GoogleLogApi class is responsible for uploading logs and authenticating to Google Drive. """

    _credentials = None
    _config = None

    def __init__(self, config: Config) -> None:

        self._config = config
        # Check if the parents ids are specified for the path in the config
        if config.get("google_drive._parents_path") is None:
            self.__set_path_parent_ids()

        if not self.auth():
            raise Exception("Could not authenticate with Google Drive")

        grouping = config.get("google_drive.grouping", config.get("grouping"))
        super().__init__(grouping)

    def __set_path_parent_ids(self) -> bool:
        """
        Sets the parent ids for the path in the config

        Returns:
            bool: whether or not the parent ids were set successfully
        """
        # Get the parent ids for the path
        path = self._config.get("google_drive.path")
        if path is None:
            raise ValueError("Directory path not specified in the config")
        if not isinstance(path, list):
            raise ValueError("Directory path must be a list")
        # Check if this is a shared drive, if so, the first item in the path will be the name of the shared drive

        drive_name = path[0]
        path = path[1:]
        parent_ids = ['root']
        if self._config.get("google_drive.is_shared_drive", False):
            # TODO: get the id of the shared drive and set it as the first parent id
            # Get the Google Drive API service resource
            parent_ids = ['root']  # TODO: Set the id of the shared drive here

        with build('drive', 'v3', credentials=self._credentials) as ds:

            for path in path:
                # Get the parent id for the current directory
                folder_id = self._find_target_document(
                    ds=ds, q=f"name='{path}' and mimeType='application/vnd.google-apps.folder' and trashed=false")
                # If the folder does not exist, create it
                if folder_id is None:
                    folder_id = self.__create_file(
                        ds=ds, title=path, parents=[parent_ids[-1]], mime_type="application/vnd.google-apps.folder")

                if folder_id is None:
                    # If the folder could not be created, return False
                    return False
                # Add the folder id to the parent ids
                parent_ids.append(folder_id)

        # Set the parent ids in the config
        self._config.put("google_drive._parents_path", parent_ids)

        return True

    def _auth(self) -> bool:
        """
        Helper function to authenticate with Google Drive, will authenticate regardless whether or not the user has already authenticated

        Returns:
            bool: whether or not the authentication was successful
        """
        client_secrets_path = os.path.normpath(
            os.path.join(ROOT_DIR, "credentials", GOOGLE_CLIENT_SECRETS_FILE))
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_path, scopes=GOOGLE_DRIVE_API_SCOPES)

        credentials = flow.run_local_server(
            host='localhost', port=8080,
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
        token_path = os.path.abspath(os.path.join(
            os.path.dirname(self._config.get_path()), "google_token.json"))
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._credentials = creds
            else:
                self._auth()  # Stores the credentials in the class
            # Save the credentials for the next run
            if self._credentials is not None:
                with open(token_path, 'w', encoding="utf8") as token:
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
        date_exists = doc['body']['content'][1]['paragraph']['elements'][0]['textRun']['content'].find(
            date) != -1

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

    def _find_target_document(self, ds: Resource, q: str) -> Union[str, None]:
        """
        Finds the target document in Google Drive using the query string

        Args:
            ds (Resource): The Google Drive API service resource
            title (str): The title of the document
            q (str): The query to search for the document

        Returns:
            str: The id of the document, or None if the document does not exist
        """

        next_page_token = None
        while True:
            items = None
            try:
                results = ds.files().list(q=q, pageToken=next_page_token).execute()
                items = results.get('files')
            except HttpError as e:
                print(e)
                return None
            if len(items) == 1:
                return items[0]['id']
            if len(items) > 1:
                raise ValueError(
                    "Multiple documents with the same title exist in the path")
            if results.get('nextPageToken') is None:
                return None

            next_page_token = results.get('nextPageToken')

    def __create_file(self, ds, title: str, parents: list, mime_type: str,) -> str:
        """
        Creates a new file in Google Drive

        Args:
            title (str): The title of the document
            parents (list): The parent folders of the document
            mimeType (str): The mime type of the document
            ds: The Google Drive service

        Returns:
            str: The id of the document
        """
        # Create the document
        file_metadata = {
            'name': title,
            'mimeType': mime_type,
            'parents': parents
        }

        file = ds.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')

    def upload_log(self, date: datetime, log_contents: str) -> bool:
        """_summary_

        Args:
            date (datetime): _description_
            log_contents (str): _description_

        Returns:
            bool: _description_
        """

        group: str = self.find_group(date)

        # Try to find the log for the given group
        print("Searching drive for log for group: " + group)
        target_log_id = None
        with build('drive', 'v3', credentials=self._credentials) as ds:
            target_log_id = self._find_target_document(
                ds=ds, q=f"name='{group}' and mimeType='application/vnd.google-apps.document' and '{self._config.get('google_drive._parents_path')[-1]}' in parents")

            if target_log_id is None:
                print("Log not found, creating new log...")
                # Creates a blank document with the title of the group, and stores the id
                # target_log_id = docs.documents().create(
                #     body={"title": group}).execute()['documentId']
                target_log_id = self.__create_file(ds=ds, title=group, parents=[self._config.get(
                    "google_drive._parents_path")[-1]], mime_type="application/vnd.google-apps.document")

        with build("docs", "v1", credentials=self._credentials) as docs:
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
