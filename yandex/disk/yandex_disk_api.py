import requests
from pprint import pprint


class YandexDisk:

    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Accept': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def get_files_list(self, params=None):
        files_url = 'https://cloud-api.yandex.net/v1/disk/resources/files'
        headers = self.get_headers()
        response = requests.get(files_url, headers=headers, params=params)
        return response.json()

    def _get_upload_link(self, disk_file_path):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": True}
        response = requests.get(upload_url, headers=headers, params=params)
        pprint(response.json())
        return response.json()

    def _get_download_link(self, disk_file_path):
        download_url = "https://cloud-api.yandex.net/v1/disk/resources/download"
        headers = self.get_headers()
        params = {"path": disk_file_path}
        response = requests.get(download_url, headers=headers, params=params)
        pprint(response.json())
        return response.json()

    def upload_local_file_to_disk(self, disk_file_path, filename):
        href = self._get_upload_link(disk_file_path=disk_file_path).get("href", "")
        response = requests.put(href, data=open(filename, 'rb'))
        # response.raise_for_status()
        if response.status_code == 201:
            print("Success")

    def upload_external_file_to_disk(self, disk_file_path, url):
        method_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

        headers = self.get_headers()
        params = {
            'path': disk_file_path,
            'url': url,
        }
        response = requests.post(method_url, headers=headers, params=params)
        response.raise_for_status()
        pprint(response.json())
        if response.status_code == 202:
            print(f'File "{disk_file_path}" was uploaded to Yandex disk')

    def download_file_from_disk(self, disk_file_path, filename):
        href = self._get_download_link(disk_file_path=disk_file_path)
        headers = self.get_headers()
        response = requests.get(href['href'], headers=headers)
        with open(filename, 'wb') as file:
            file.write(response.content)
        response.raise_for_status()
        if response.status_code == 200:
            print("Success")

    def create_new_folder(self, path):
        method_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {'path': path}
        response = requests.put(method_url, headers=headers, params=params)
        if response.status_code == 201:
            print(f'New folder "{path}" is created')
        if response.json().get('error') == 'DiskPathPointsToExistentDirectoryError':
            print(f'Directory "{path}" already exists on Yandex disk')
