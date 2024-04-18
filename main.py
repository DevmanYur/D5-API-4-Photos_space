import os
from os.path import splitext
import time
import random
import requests
from pathlib import Path
from urllib.parse import urlparse
import telegram
from dotenv import load_dotenv


def download_photo(name_photo, photo_url, name_folder):
    photo_format = get_photo_format(photo_url)
    response = requests.get(photo_url)
    response.raise_for_status()

    folder_path = os.path.join(name_folder, name_photo)
    photo_path = f'{folder_path}{photo_format}'
    with open(photo_path, 'wb') as file:
        file.write(response.content)


def get_photo_format(photo_url):
    photo_path, photo_format = splitext(urlparse(photo_url).path)
    return photo_format


def get_id_last_launch_spacex_with_pictures(all_launches):
    for launch in all_launches[::-1]:
        if launch["links"]["flickr"]["original"]:
            return launch["id"]


def get_photos_last_launch_spacex(name_folder):
    all_launches_url = 'https://api.spacexdata.com/v5/launches/'
    response = requests.get(all_launches_url)
    response.raise_for_status()
    all_launches = response.json()
    last_launch_id = get_id_last_launch_spacex_with_pictures(all_launches)

    last_launch_url = f'https://api.spacexdata.com/v5/launches/{last_launch_id}'
    last_launch_response = requests.get(last_launch_url)
    last_launch_response.raise_for_status()
    last_launch = last_launch_response.json()["links"]["flickr"]["original"]
    for number, photo_url in enumerate(last_launch):
        name_photo = f'spacex_{number}'
        download_photo(name_photo, photo_url, name_folder)


def get_apod_nasa_photos(name_folder, nasa_token, start_date, end_date):
    payload = {"api_key": f'{nasa_token}',
               "start_date": f'{start_date}',
               "end_date": f'{end_date}'
               }
    response = requests.get('https://api.nasa.gov/planetary/apod', params = payload)
    response.raise_for_status()

    all_launches = response.json()
    for numder, launch in enumerate(all_launches):
        photo_url = launch["url"]
        if get_photo_format(photo_url):
            name_photo = f'nasa_apod_{numder}'
            download_photo(name_photo, photo_url, name_folder)


def get_epic_nasa_photos(name_folder, nasa_token):
    payload = {"api_key": f'{nasa_token}'}
    response = requests.get('https://api.nasa.gov/EPIC/api/natural/images', params=payload)
    response.raise_for_status()
    all_epic_photos = response.json()

    for numder, photo in enumerate(all_epic_photos):
        year, month , day_time  = photo["date"].split('-')
        day, time = day_time.split(' ')
        name_file = photo["image"]
        epic_photo_response = requests.get(f'https://api.nasa.gov/EPIC/archive/natural/{year}/{month}/{day}/png/{name_file}.png',
                                           params=payload)
        epic_photo_response.raise_for_status()
        photo_url = epic_photo_response.url
        if get_photo_format(photo_url):
            name_photo = f'nasa_epic_{numder}'
            download_photo(name_photo, photo_url, name_folder)


def start_telegram_bot(path_image, telegram_token):
    bot = telegram.Bot(token=telegram_token)
    chat_id = bot.get_updates()[0].message.from_user.id
    bot.send_document(chat_id=chat_id, document=open(path_image, 'rb'))


def main():
    load_dotenv()
    nasa_token = os.environ['NASA_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']

    name_folder = os.getenv('NAME_FOLDER', 'images')
    nasa_start_date = os.getenv('NASA_START_DATE', '2024-01-01')
    nasa_end_date = os.getenv('NASA_END_DATE', '2024-01-15')
    delay_in_hours = int(os.getenv('DELAY_IN_HOURS', '4'))

    Path(name_folder).mkdir(parents=True, exist_ok=True)

    get_photos_last_launch_spacex(name_folder)
    get_apod_nasa_photos(name_folder, nasa_token, nasa_start_date, nasa_end_date)
    get_epic_nasa_photos(name_folder, nasa_token)

    while True:
        for address, dirs, files in os.walk(name_folder):
            random.shuffle(files)
            for name in files:
                path_image = os.path.join(address, name)
                start_telegram_bot(path_image, telegram_token)
        time.sleep(3600*delay_in_hours)


if __name__ == '__main__':
    main()
