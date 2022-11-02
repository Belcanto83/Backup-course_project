import pytest
import json
import os
from yandex.disk.yandex_disk_api import YandexDisk

FIXTURE_YA_DISK_FOLDERS = [
    'test_folder_1',
    'test_folder_2',
    'test_folder_3',
]


# @pytest.fixture()
# def ya_d_preparation():
#     print('Start')
#     yield
#     print('End')


@pytest.mark.parametrize('file_path', FIXTURE_YA_DISK_FOLDERS)
def test_create_new_folder(file_path):
    ya_d_token_path = os.pardir + '/info_not_for_git/Ya_D.json'
    with open(ya_d_token_path) as file:
        data = json.load(file)
    ya_d_token = data['token']
    ya_disk = YandexDisk(token=ya_d_token)

    test_folder_path = f'VK_photos/{file_path}'

    status_code = ya_disk.create_new_folder(test_folder_path)
    assert status_code == 201

    status_code = ya_disk.get_file_metadata(test_folder_path)
    assert status_code == 200

    status_code = ya_disk.delete_file(test_folder_path)
    assert status_code == 204
