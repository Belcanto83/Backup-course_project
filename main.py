import requests
from datetime import datetime
import json
import logging
from pprint import pprint
from progress.bar import IncrementalBar
from progress_bar.custom_bars import ProgressBar
from yandex.disk.yandex_disk_api import YandexDisk


class BackupPhotosFromVK:
    base_url = 'https://api.vk.com/method/'
    backup_folder = 'API_python_uploads/VK_photos'

    def __init__(self, token, target, vk_api_version='5.131', backup_folder=backup_folder):
        self.params = dict(access_token=token, v=vk_api_version)
        # probably, not necessary here
        self.backup_target = target
        self.backup_folder = backup_folder
        self.backup_target.create_new_folder(self.backup_folder)

    def backup_user_profile_photos(self, vk_user_id, photos_count=5):
        # probably, 'backup_target' should be here
        method_url = self.base_url + 'photos.get'
        method_params = {
            'owner_id': vk_user_id,
            'album_id': 'profile',
            'extended': True,
            'photo_sizes': True,
            'rev': True,
            'count': photos_count,
        }
        all_params = {**self.params, **method_params}
        # Получили инфу о фотографиях пользователя в профиле. Можно реализовать это отдельным методом.
        response = requests.get(method_url, params=all_params).json()['response']

        user_profile_photos = [photo for photo in response['items']]

        # print('Photos from VK user profile:')
        # pprint(user_profile_photos)

        # Сформируем словарь вида: {photo_name: {photo_obj}}
        user_profile_photos_obj = {}
        for photo in user_profile_photos:
            file_path = photo['sizes'][0]['url'].split('?')[0]
            file_extension = '.' + file_path.rsplit('.', 1)[1]
            file_name = str(photo['likes']['count'])
            if file_name + file_extension in user_profile_photos_obj:
                file_name += f"_{datetime.fromtimestamp(photo['date']).strftime('%d-%m-%Y_%Hh%Mm')}"
            file_name += file_extension
            user_profile_photos_obj[file_name] = photo

        # Создадим папку с названием по "id" пользователя "VK"
        self.backup_target.create_new_folder(f'{self.backup_folder}/{vk_user_id}')

        # bar = IncrementalBar('Copying files to disk:', max=len(user_profile_photos_obj))
        file_names = [f'{self.backup_folder}/{vk_user_id}/{photo_name}' for photo_name in user_profile_photos_obj]
        # print(file_names)
        bar = ProgressBar('Copying files to disk:', max=len(user_profile_photos_obj), file_names=file_names)

        data_for_file = []
        # Скопируем полученные фотографии в указанный "backup_target"
        for photo_name, photo_obj in user_profile_photos_obj.items():
            # Выбираем фото с макс. разрешением: max(width x height)
            # print(photo_obj)
            max_photo_size = max(photo_obj['sizes'], key=lambda itm: itm.get('width') * itm.get('height'))
            photo_url = max_photo_size['url']

            bar.next()
            self.backup_target.upload_external_file_to_disk(f'{self.backup_folder}/{vk_user_id}/{photo_name}', photo_url)

            # Запишем информацию о скопированной на диск фотографии в ".json" файл
            photo_data = {
                "file_name": photo_name,
                "size": f'{max_photo_size["width"]}x{max_photo_size["height"]}'
            }
            data_for_file.append(photo_data)

        bar.finish()

        with open('saved_photos.json', 'w') as file_obj:
            json.dump(data_for_file, file_obj, indent=2)


if __name__ == '__main__':
    with open('info_not_for_git/VK.json') as file:
        data = json.load(file)
    vk_token = data['token']

    with open('info_not_for_git/Ya_D.json') as file:
        data = json.load(file)
    ya_d_token = data['token']

    logger = logging.getLogger('main')
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler('backup.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    backup_target = YandexDisk(token=ya_d_token)
    backuper = BackupPhotosFromVK(token=vk_token, target=backup_target)

    user_id = str(input('Please enter VK user id: '))
    backuper.backup_user_profile_photos(user_id)
    # backuper.backup_user_profile_photos('230101')
