import requests
from datetime import datetime
import time
import json
import logging
# from pprint import pprint
# from progress.bar import IncrementalBar
from progress_bar.custom_bars import ProgressBar
from yandex.disk.yandex_disk_api import YandexDisk


class BackupPhotosFromVK:
    base_url = 'https://api.vk.com/method/'
    backup_folder = 'VK_photos'

    def __init__(self, token, target, vk_api_version='5.131', backup_folder=backup_folder):
        self.params = dict(access_token=token, v=vk_api_version)
        # probably, not necessary here
        self.backup_target = target
        self.backup_folder = backup_folder
        self.backup_target.create_new_folder(self.backup_folder)

    def get_user(self, vk_user_id):
        method_url = self.base_url + 'users.get'
        method_params = {
            'user_ids': vk_user_id,
        }
        all_params = {**self.params, **method_params}
        response = requests.get(method_url, params=all_params).json()
        return response['response'][0]

    def get_user_albums(self, vk_user_id, albums_count=3):
        method_url = self.base_url + 'photos.getAlbums'
        method_params = {
            'owner_id': vk_user_id,
            'count': albums_count
        }
        all_params = {**self.params, **method_params}
        response = requests.get(method_url, params=all_params).json()
        # print(response)
        return response.get('response')

    def get_user_photos(self, vk_user_id, album_id, photos_count):
        method_url = self.base_url + 'photos.get'
        method_params = {
            'owner_id': vk_user_id,
            'album_id': str(album_id),
            'extended': True,
            'photo_sizes': True,
            'rev': True,
            'count': photos_count,
        }
        all_params = {**self.params, **method_params}
        response = requests.get(method_url, params=all_params).json().get('response')
        return response

    def backup_user_album_photos(self, vk_user_id, album_id='profile', album_title="without-title", photos_count=5):
        # probably, 'backup_target' should be here

        # Получили инфу о фотографиях пользователя в профиле
        response = self.get_user_photos(vk_user_id, album_id, photos_count)
        if response is None or response['count'] == 0:
            return

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

        user = self.get_user(vk_user_id)

        # Создадим папку с названием по "id" пользователя "VK"
        self.backup_target.create_new_folder(f'{self.backup_folder}/'
                                             f'{vk_user_id}_{user["first_name"]}_{user["last_name"]}/')
        self.backup_target.create_new_folder(f'{self.backup_folder}/'
                                             f'{vk_user_id}_{user["first_name"]}_{user["last_name"]}/'
                                             f'{album_id}_{album_title}')

        # bar = IncrementalBar('Copying files to disk:', max=len(user_profile_photos_obj))
        file_names = [f'{self.backup_folder}/{vk_user_id}_{user["first_name"]}_{user["last_name"]}/'
                      f'{album_id}_{album_title}/{photo_name}'
                      for photo_name in user_profile_photos_obj]
        # print(file_names)
        bar = ProgressBar('Copying files to disk:', max=len(user_profile_photos_obj), file_names=file_names)

        data_for_file = []
        # Скопируем полученные фотографии в указанный "backup_target"
        for photo_name, photo_obj in user_profile_photos_obj.items():
            # Выбираем фото с макс. разрешением: max(width x height)
            if photo_obj['sizes'][0]['width'] != 0:
                max_photo_size = max(photo_obj['sizes'], key=lambda itm: itm.get('width') * itm.get('height'))
            else:
                max_photo_size = photo_obj['sizes'][-1]

            photo_url = max_photo_size['url']

            bar.next()
            self.backup_target.upload_external_file_to_disk(f'{self.backup_folder}/'
                                                            f'{vk_user_id}_{user["first_name"]}_{user["last_name"]}/'
                                                            f'{album_id}_{album_title}/{photo_name}', photo_url)

            # Запишем информацию о скопированной на диск фотографии в ".json" файл
            photo_data = {
                "file_name": photo_name,
                "size": f'{max_photo_size["width"]}x{max_photo_size["height"]}'
            }
            data_for_file.append(photo_data)

        bar.finish()

        with open('saved_photos.json', 'w') as file_obj:
            json.dump(data_for_file, file_obj, indent=2)

    def backup_user_photo_albums(self, vk_user_id, albums_count=10, photos_count=5):
        user_albums_obj = self.get_user_albums(vk_user_id=vk_user_id, albums_count=albums_count)
        if user_albums_obj is None:
            return
        user_albums = user_albums_obj['items']
        for user_album in user_albums:
            self.backup_user_album_photos(vk_user_id=vk_user_id, album_id=user_album['id'],
                                          album_title=user_album['title'], photos_count=photos_count)
            time.sleep(0.35)


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
    backuper.backup_user_album_photos(user_id, album_id='profile')
    # backuper.backup_user_album_photos(user_id, '140491119')
    backuper.backup_user_photo_albums(user_id, albums_count=10)
    # backuper.backup_user_profile_photos('230101')
