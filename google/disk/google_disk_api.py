from __future__ import print_function

import os.path
import io
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

import logging
from pprint import pprint


class GoogleDisk:
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('info_not_for_git/google_token.json'):
            creds = Credentials.from_authorized_user_file('info_not_for_git/google_token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'info_not_for_git/google_credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('info_not_for_git/google_token.json', 'w') as token:
                token.write(creds.to_json())
        self.creds = creds
        self.logger = logging.getLogger('main.google.disk.google_disk_api')
        self.file_cache = {}

    def get_folders(self):
        try:
            service = build('drive', 'v3', credentials=self.creds)

            # get all files from disk
            drive_files = service.files().list(fields="files(id, name, parents, mimeType)").execute()
            all_items = drive_files.get('files', [])
            drive_folders = list(filter(lambda itm: itm['mimeType'] == 'application/vnd.google-apps.folder', all_items))
            return drive_folders
        except HttpError as error:
            print(F'An error occurred: {error}')
            self.logger.error(F'An error occurred: {error}')

    def _get_parent_ids(self, folders, path):
        dirs = path.split('/')
        if len(dirs) == 1:
            child = dirs[-1]
            children = list(filter(lambda itm: itm['name'] == child, folders))
            return children
        child = dirs[-1]
        path = '/'.join(dirs[:-1])

        parents = self._get_parent_ids(folders, path)
        children = list(filter(lambda itm: itm['name'] == child, folders))
        proof_children = []
        for child_folder in children:
            for parent_folder in parents:
                if child_folder['parents'][0] == parent_folder['id']:
                    proof_children.append(child_folder)
        # print(path, proof_children)
        return proof_children

    def upload_external_file_to_disk(self, disk_file_path, url):
        try:
            service = build('drive', 'v3', credentials=self.creds)
            # Get remote file data from url
            file_data = requests.get(url).content

            # Call the Drive v3 API
            drive_folders = self.get_folders()
            file_metadata = {
                'name': disk_file_path.split('/')[-1],
                'mimeType': 'image/jpeg',
                'parents': [self._get_parent_ids(drive_folders, '/'.join(disk_file_path.split('/')[:-1]))[0]['id']]
            }
            # print('disk_file_path: ', '/'.join(disk_file_path.split('/')[:-1]))
            # print('parents: ', file_metadata['parents'])
            fh = io.BytesIO(file_data)
            # media = MediaIoBaseUpload(fh, mimetype='image/jpeg', chunksize=1024*1024)
            media = MediaIoBaseUpload(fh, mimetype='image/jpeg')
            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, media_body=media,
                                          fields='id').execute()
            # print(F'File ID: {file.get("id")}')
            self.logger.info(f'File "{disk_file_path}" is uploaded to Google disk')
            return file.get('id')

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')

    def create_new_folder(self, path):
        """ Create a folder
        Returns : Folder Id
        """

        new_folder_name = path.split('/')[-1]
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.creds)

            # get all files from disk
            drive_folders = self.get_folders()
            # pprint(drive_folders)

            # Define parent folder for new folder
            target_folder = self._get_parent_ids(drive_folders, path)
            # print('target_folder: ', target_folder)

            if not target_folder:
                parent_folder = self._get_parent_ids(drive_folders, '/'.join(path.split('/')[:-1]))
                if parent_folder or len(path.split('/')) == 1:
                    parent_folder_id = parent_folder[0]['id'] if parent_folder else 'root'

                    file_metadata = {
                        'name': new_folder_name,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [parent_folder_id]
                    }

                    # pylint: disable=maybe-no-member
                    file = service.files().create(body=file_metadata, fields='id').execute()
                    print(F'New folder "{path}" is created')
                    self.logger.info(F'New folder "{path}" is created')
                    self.file_cache[path] = file.get("id")

                    return file.get('id')

                else:
                    print(f'Specified "path: {path}" does not exist')
                    self.logger.error(f'Specified "path: {path}" does not exist')

            else:
                print(f'Directory "{path}" already exists on Google disk')

        except HttpError as error:
            print(F'An error occurred: {error}')
            self.logger.error(F'An error occurred: {error}')
