import os
from os.path import splitext
import time
import random
import requests
from pathlib import Path
from urllib.parse import urlparse
import telegram
from dotenv import load_dotenv


def download_function(name_photo, url_photo, name_folder):
    format_photo = get_format_photo(url_photo)
    response = requests.get(url_photo)
    response.raise_for_status()

    Path(name_folder).mkdir(parents=True, exist_ok=True)
    path_folder = os.path.join(name_folder, name_photo)
    path_photo = f'{path_folder}{format_photo}'
    with open(path_photo, 'wb') as file:
        file.write(response.content)


def get_format_photo(url_photo):
    path_photo, format_photo = splitext(urlparse(url_photo).path)
    return format_photo


def get_id_last_launch_spacex_with_pictures(all_launches):
    for launch in all_launches[::-1]:
        if launch["links"]["flickr"]["original"]:
            return launch["id"]
            break


def get_photos_last_launch_spacex(name_folder):
    url_all_launches = 'https://api.spacexdata.com/v5/launches/'
    response = requests.get(url_all_launches)
    response.raise_for_status()
    all_launches = response.json()
    id_last_launch = get_id_last_launch_spacex_with_pictures(all_launches)

    url_last_launch = f'https://api.spacexdata.com/v5/launches/{id_last_launch}'
    response_last_launch = requests.get(url_last_launch)
    response_last_launch.raise_for_status()
    last_launch = response_last_launch.json()["links"]["flickr"]["original"]
    for number, url_photo in enumerate(last_launch):
        name_photo = f'spacex_{number}'
        download_function(name_photo, url_photo, name_folder)


def get_apod_photos_nasa(name_folder, nasa_token, start_date, end_date):
    payload = {"api_key": f'{nasa_token}',
               "start_date": f'{start_date}',
               "end_date": f'{end_date}'
               }
    response = requests.get('https://api.nasa.gov/planetary/apod', params = payload)
    response.raise_for_status()

    all_launches = response.json()
    for numder, launch in enumerate(all_launches):
        url_photo = launch["url"]
        if get_format_photo(url_photo):
            name_photo = f'nasa_apod_{numder}'
            download_function(name_photo, url_photo, name_folder)


def get_epic_photos_nasa(name_folder, nasa_token):
    payload = {"api_key": f'{nasa_token}'}
    response = requests.get('https://api.nasa.gov/EPIC/api/natural/images', params=payload)
    response.raise_for_status()
    all_epic_photos = response.json()

    for numder, photo in enumerate(all_epic_photos):
        year, month , day_time  = photo["date"].split('-')
        day, time = day_time.split(' ')
        name_file = photo["image"]
        response_epic_photo = requests.get(f'https://api.nasa.gov/EPIC/archive/natural/{year}/{month}/{day}/png/{name_file}.png',
                                           params=payload)
        response_epic_photo.raise_for_status()
        url_photo = response_epic_photo.url
        if get_format_photo(url_photo):
            name_photo = f'nasa_epic_{numder}'
            download_function(name_photo, url_photo, name_folder)


def start_telegram(path_image, telegram_token):
    bot = telegram.Bot(token=telegram_token)
    chat_id = bot.get_updates()[0].message.from_user.id
    bot.send_document(chat_id=chat_id, document=open(path_image, 'rb'))


def main():
    load_dotenv()
    nasa_token = os.environ['NASA_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']

    name_folder = os.getenv('NAME_FOLDER', 'images')
    start_date_nasa = os.getenv('START_DATE_NASA', '2024-01-01')
    end_date_nasa = os.getenv('END_DATE_NASA', '2024-01-15')
    delay_in_hours = int(os.getenv('DELAY_IN_HOURS', '4'))

    get_photos_last_launch_spacex(name_folder)
    get_apod_photos_nasa(name_folder, nasa_token, start_date_nasa, end_date_nasa)
    get_epic_photos_nasa(name_folder, nasa_token)

    while True:
        for address, dirs, files in os.walk(name_folder):
            random.shuffle(files)
            for name in files:
                path_image = os.path.join(address, name)
                start_telegram(path_image, telegram_token)
        time.sleep(3600*delay_in_hours)


if __name__ == '__main__':
    main()
