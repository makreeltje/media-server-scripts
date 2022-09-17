import json
import math
import os
import time
import pandas
from datetime import datetime
from termcolor import colored

import requests

dry_run = False


def set_variables():
    radarr_url = os.environ.get("RADARR_URL")
    radarr_api_key = os.environ.get("RADARR_API_KEY")
    sonarr_url = os.environ.get("SONARR_URL")
    sonarr_api_key = os.environ.get("SONARR_API_KEY")
    tautulli_url = os.environ.get("TAUTULLI_URL")
    tautulli_api_key = os.environ.get("TAUTULLI_API_KEY")
    overseerr_url = os.environ.get("OVERSEERR_URL")
    overseerr_api_key = os.environ.get("OVERSEERR_API_KEY")
    plex_url = os.environ.get("PLEX_URL")
    plex_auth_token = os.environ.get("PLEX_AUTH_TOKEN")

def check_environment(key, value):
    if(len(value) == 0):
        

def execute_script():
    print(colored('This is a script that removes old media from your Plex library trough Radarr and Sonarr based on '
                  'the given threshold. It will ask for your Radarr, Sonarr, Tautulli and Plex url and API key/Auth '
                  'token.', attrs=['bold']))

    # radarr_url = input(colored('Please enter your Radarr url: ', 'yellow'))
    # radarr_api_key = input(colored('Please enter your Radarr API key: ', 'yellow'))
    # sonarr_url = input(colored('Please enter your Sonarr url: ', 'yellow'))
    # sonarr_api_key = input(colored('Please enter your Sonarr API key: ', 'yellow'))
    # tautulli_url = input(colored('Please enter your Tautulli url: ', 'yellow'))
    # tautulli_api_key = input(colored('Please enter your Tautulli API key: ', 'yellow'))
    threshold = input(colored('Enter the threshold in days (ex. 1 year = 365, 2 years = 730 etc.): ', 'yellow'))
    tautulli_url = 'https://tautulli.meelsnet.nl/'
    tautulli_api_key = '9af60987061945f397bca59eb114e5bc'
    radarr_url = 'https://movies.meelsnet.nl/'
    radarr_api_key = 'c7ceb5496f2a40b3ac4787fc468ec6f9'
    review = input(colored('Do you want to review the results? (y/n): ', 'yellow'))

    merged_df = get_tautulli_libraries_table(threshold, tautulli_url, tautulli_api_key, radarr_url, radarr_api_key)

    if review.lower() == 'y':
        print(merged_df.to_string())
        delete = input(colored('Do you want to delete the media? (y/n): ', 'yellow'))
        if delete.lower() == 'y':
            print(colored('Deleting media...', 'red'))
            delete_movie(merged_df, radarr_url, radarr_api_key)
        else:
            print(colored('Skipping...', 'green'))
            return


def get_tautulli_libraries_table(threshold, tautulli_url, tautulli_api_key, radarr_url, radarr_api_key):
    print(colored('Getting Tautulli Libraries', attrs=['bold']))
    url = '{}api/v2' \
          '?apikey={}' \
          '&cmd=get_libraries_table'.format(tautulli_url, tautulli_api_key)
    print(url)
    response = requests.get(url)
    # print(response.json())

    for data in response.json()['response']['data']['data']:
        section_name = data['section_name']
        section_id = data['section_id']
        rating_key = data['rating_key']
        section_type = data['section_type']

        if section_type == 'live':
            continue

        print('{}\nSection id ({})\nRating key ({})\nMedia type ({})'
              .format(section_name, section_id, rating_key, section_type))

        choice = input(colored('Do you want to get the library media info for this section? (y/n): ', 'yellow'))
        if choice.lower() == 'y':
            return get_tautulli_library_media_info(threshold, section_name, section_id, section_type, tautulli_url,
                                                   tautulli_api_key, radarr_url, radarr_api_key)
        else:
            print(colored('Skipping\n', 'red'))


def get_tautulli_library_media_info(threshold, section_name, section_id, section_type, tautulli_url, tautulli_api_key,
                                    radarr_url, radarr_api_key):
    tautulli_library_media_info = []
    start = 0

    print(colored('Getting Tautulli Library Media Info for ({})'.format(section_name), attrs=['bold']))
    url = '{}api/v2' \
          '?apikey={}' \
          '&cmd=get_library_media_info' \
          '&section_id={}' \
          '&order_column={}' \
          '&order_dir={}' \
          '&start={}' \
        .format(tautulli_url, tautulli_api_key, section_id, 'last_played', 'desc', '0')
    response = requests.get(url)

    total_records = response.json()['response']['data']['recordsTotal']

    print(colored('Total records: {}'.format(total_records), 'grey'))

    if section_type == 'movie':
        headers = ["Title", "Added at", "Last played", "Play count", "Size"]
        radarr_movie_list = get_radarr_movies(radarr_url, radarr_api_key)
    elif section_type == 'show':
        headers = ["Title", "Added at", "Last played", "Play count", "Size"]
        sonarr_series_list = get_sonarr_series()

    while start < total_records:
        url = '{}api/v2' \
              '?apikey={}' \
              '&cmd=get_library_media_info' \
              '&section_id={}' \
              '&refresh=true' \
              '&order_column={}' \
              '&order_dir={}' \
              '&start={}' \
            .format(tautulli_url, tautulli_api_key, section_id, 'last_played', 'desc', start)

        response = requests.get(url)

        for data in response.json()['response']['data']['data']:
            title = data['title']

            added_at = datetime.fromtimestamp(int(data['added_at']))
            last_played = data['last_played']
            play_count = data['play_count']
            file_size = str(data['file_size'])

            if last_played is not None:
                last_played = math.trunc((time.time() - float(last_played)) / (60 * 60 * 24))
                if last_played < int(threshold):
                    continue

                last_played = str(last_played) + ' days ago'
            else:
                threshold_calculation = math.trunc((time.time() - float(data['added_at'])) / (60 * 60 * 24))
                if threshold_calculation < int(threshold):
                    continue

            if play_count is not None:
                play_count = str(play_count)

            tautulli_library_media_info.append([title, added_at, last_played, play_count, file_size])

        start = start + 25

    # print(response.json())
    tautulli_library_media_info = generate_pandas_dataframe(tautulli_library_media_info, headers)

    merged_df = merge_pandas_dataframes(tautulli_library_media_info, radarr_movie_list)

    return merged_df;


def get_human_readable_size(size, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}{suffix}"
        size /= 1024.0
    return f"{size:.1f}Yi{suffix}"


def generate_pandas_dataframe(results, headers):
    df = pandas.DataFrame(results, columns=headers)
    # print(df.to_string())
    return df


def merge_pandas_dataframes(df1, df2):
    return pandas.merge(df1, df2, on='Size', how='inner')


def get_radarr_movies(radarr_url, radarr_api_key):
    radarr_movie_list = []
    print('Getting Radarr Movies')
    url = '{}api/v3/movie' \
          '?apikey={}'.format(radarr_url, radarr_api_key)
    response = requests.get(url)
    # print(response.json())

    for data in response.json():

        if data['sizeOnDisk'] == 0:
            continue
        else:
            file_size = str(data['sizeOnDisk'])

        tmdb_id = data['movieFile']['movieId']

        headers = ["Size", "Id"]
        radarr_movie_list.append([file_size, tmdb_id])
    pandas_radarr_movie_list = generate_pandas_dataframe(radarr_movie_list, headers)
    return pandas_radarr_movie_list
    # print(response.json())


def get_sonarr_series():
    return None


def delete_movie(merged_df, radarr_url, radarr_api_key):
    for index, row in merged_df.iterrows():
        print('Deleteing {}'.format(row['Title']))
        url = '{}api/v3/movie/{}' \
              '?deleteFiles=true' \
              '&addImportExclusion=false' \
              '&apikey={}'.format(radarr_url, row['Id'], radarr_api_key)
        print(url)
        response = requests.delete(url)
        if response.status_code == 200:
            continue
        else:
            print(colored('Error deleting movie file {}'.format(row['Title']), 'red'))
            print(response.json())
            break