#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Delete media from server based on time last watched, or if never played based on time added based on threshold
"""

from __future__ import print_function
from __future__ import unicode_literals

import datetime
import logging
import re
from datetime import time

import requests
from os import environ
from dotenv import load_dotenv

load_dotenv()

# EDIT PARAMETERS IN .env FILE #
PLEX_URL = environ.get('PLEX_URL')
PLEX_TOKEN = environ.get('PLEX_TOKEN')
RADARR_URL = environ.get('RADARR_URL')
RADARR_APIKEY = environ.get('RADARR_APIKEY')
SONARR_URL = environ.get('SONARR_URL')
SONARR_APIKEY = environ.get('SONARR_APIKEY')
OVERSEERR_URL = environ.get('OVERSEERR_URL')
OVERSEERR_APIKEY = environ.get('OVERSEERR_APIKEY')
TAUTULLI_URL = environ.get('TAUTULLI_URL')
TAUTULLI_APIKEY = environ.get('TAUTULLI_APIKEY')

LIBRARY_NAMES = ['Movies', 'TV Shows', 'Animation', 'Series']

REMOVE_LIMIT = 365*3  # Days
DRY_RUN = True

headers = {
    'Accept': 'application/json'
}

logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)

# CODE BELOW #


def get_plex_libraries():
    logging.info('📦 Retrieving Plex libraries from Plex endpoint')


    payload = {
        'X-Plex-Token': PLEX_TOKEN
    }

    try:
        r = requests.get(PLEX_URL.rstrip('/') + '/library/sections/', params=payload, headers=headers)
        response = r.json()
        logging.debug('get_plex_libraries response: ' + str(response))

        res_data = response['MediaContainer']['Directory']
        if len(res_data) == 0:
            logging.warning('🚧 No Plex libraries found')
        else:
            logging.info('✅ Retrieved {} Plex libraries'.format(len(res_data)))
        return res_data
    except Exception as e:
        logging.error('❌ Plex API \'get_libraries\' request failed: {0}'.format(e))


def parse_plex_library_result(payload):
    result = {
        'library_id': payload['key'],
        'type': payload['type'],
        'name': payload['title']
    }

    return result

def get_plex_media_info(parsed_tautulli_library):
    logging.info('📦 Retrieving Plex media info from Plex endpoint')

    payload = {
        'X-Plex-Token': PLEX_TOKEN
    }

    try:
        r = requests.get(PLEX_URL.rstrip('/') + '/library/sections/{0}/all'.format(parsed_tautulli_library['section_id']), params=payload, headers=headers)
        response = r.json()
        logging.debug('get_plex_media_info response: ' + str(response))

        res_data = response['MediaContainer']['Metadata']
        if len(res_data) == 0:
            logging.warning('🚧 No Plex media info found for library {}'.format(parsed_tautulli_library['section_name']))
        else:
            logging.info('✅ Retrieved {} {} media info from Plex'.format(len(res_data), parsed_tautulli_library['section_name']))
        return res_data
    except Exception as e:
        logging.error('❌ Plex API \'get_libraries\' request failed: {0}'.format(e))


def get_radarr_movies():
    logging.info('📦 Retrieving Radarr movies from Radarr endpoint')

    payload = {
        'apikey': RADARR_APIKEY,
    }

    try:
        r = requests.get(RADARR_URL.rstrip('/') + '/api/v3/movie', params=payload)
        response = r.json()
        logging.debug('get_radarr_movies response: ' + str(response))

        if len(response) == 0:
            logging.warning('🚧 No Radarr movies found')
        else:
            logging.info('✅ Retrieved {} Radarr movies'.format(len(response)))

        return response
    except Exception as e:
        logging.error('❌ Radarr API \'movie\' request failed: {0}'.format(e))


def remove_radarr_movies_without_files(radarr_movie_list):
    logging.info('📦 Removing Radarr movies without files')

    items_to_remove = []

    for radarr_item in radarr_movie_list:
        if 'movieFile' not in radarr_item:
            items_to_remove.append(radarr_item)

    for item in items_to_remove:
        radarr_movie_list.remove(item)
        logging.debug('✅ Removed {} from Radarr movie list'.format(item['title']))

    return radarr_movie_list


def get_sonarr_series():
    logging.info('📦 Retrieving Sonarr series from Sonarr endpoint')

    payload = {
        'apikey': SONARR_APIKEY,
    }

    try:
        r = requests.get(SONARR_URL.rstrip('/') + '/api/v3/series', params=payload)
        response = r.json()
        logging.debug('get_sonarr_series response: ' + str(response))

        if len(response) == 0:
            logging.warning('🚧 No Sonarr series found')
        else:
            logging.info('✅ Retrieved {} Sonarr series'.format(len(response)))

        return response
    except Exception as e:
        logging.error('❌ Sonarr API \'series\' request failed: {0}'.format(e))


def get_overseerr_requests():
    logging.info('📦 Retrieving Overseerr media from Overseerr endpoint')

    payload = {
        'take': 20,
        'skip': 0,
        'sort': 'added'
    }

    headers = {
        'X-Api-Key': OVERSEERR_APIKEY,
    }

    try:
        r = requests.get(OVERSEERR_URL.rstrip('/') + '/api/v1/request',params=payload, headers=headers)
        response = r.json()
        logging.debug('get_overseerr_requests response: ' + str(response))

        results = response['pageInfo']['results']
        res_data = response['results']
        while results > payload['skip']:
            payload['skip'] = payload['skip'] + 20
            r = requests.get(OVERSEERR_URL.rstrip('/') + '/api/v1/request', params=payload, headers=headers)
            response = r.json()
            for result in response['results']:
                res_data.append(result)

        logging.info('✅ Retrieved {} requests from Overseerr'.format(len(res_data)))
        return res_data
    except Exception as e:
        logging.error('❌ Overseerr API \'request\' request failed: {0}'.format(e))

def get_tautulli_libraries_table():
    logging.info('📦 Retrieving Tautulli libraries from Tautulli endpoint')

    payload = {
        'apikey': TAUTULLI_APIKEY,
        'cmd': 'get_libraries_table'
    }

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        logging.debug('get_tautulli_libraries_table response: ' + str(res_data))

        if len(res_data) == 0:
            logging.warning('🚧 No Tautulli libraries found')
        else:
            logging.info('✅ Retrieved {} Tautulli libraries'.format(len(res_data)))
        return res_data
    except Exception as e:
        logging.error("❌ Tautulli API 'get_libraries_table' request failed: {0}".format(e))


def parse_tautulli_libraries_table(payload):
    result = {
        'section_name': payload['section_name'],
        'section_id': payload['section_id'],
        'rating_key': payload['rating_key'],
        'section_type': payload['section_type'],
        'count': payload['count'],
    }

    if result['section_type'] == 'live':
        logging.warning('🚧 Skipping live section: {}'.format(result['section_name']))
        return None
    return result


def get_tautulli_library_media_info(tautulli_library):
    logging.info('📦 Retrieving Tautulli library {} media info'.format(tautulli_library['section_name']))

    payload = {
        'apikey': TAUTULLI_APIKEY,
        'cmd': 'get_library_media_info',
        'section_id': tautulli_library['section_id'],
        'order_column': 'last_played',
        'order_dir': 'desc',
        'length': 100,
        'start': 0
    }

    res_data = []

    try:
        while payload['start'] < tautulli_library['count']:
            r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
            response = r.json()

            logging.debug('get_tautulli_library_media_info response: ' + str(res_data))

            if len(response['response']['data']['data']) == 0:
                logging.warning('🚧 No Tautulli library {} media found'.format(tautulli_library['section_name']))
            else:
                for media in response['response']['data']['data']:
                    res_data.append(media)
            payload['start'] = payload['start'] + 100

        logging.info('✅ Retrieved {} {} media info from Tautulli'.format(len(res_data), tautulli_library['section_name']))
        return res_data
    except Exception as e:
        logging.error("❌ Tautulli API 'get_tautulli_library_media_info' request failed: {0}".format(e))


def merge_plex_tautulli_media_info(tautulli_media_info, plex_media_info, library):
    logging.info('📦 Merging {} Plex and Tautulli media info'.format(library['section_name']))
    merged_media_info = []

    for plex_media in plex_media_info:
        for tautulli_media in tautulli_media_info:
            if reformat_name(tautulli_media['title']) == reformat_name(plex_media['title']):
                if library['section_type'] == 'movie':
                    merged_media_info.append(merge_plex_tautulli_movie_media_info(tautulli_media, plex_media))
                elif library['section_type'] == 'show':
                    merged_media_info.append(merge_plex_tautulli_show_media_info(tautulli_media, plex_media))


    logging.debug('merge_plex_tautulli_media_info response: ' + str(merged_media_info))
    logging.info('✅ Merged {} Plex and Tautulli media info'.format(library['section_name']))
    return merged_media_info


def reformat_name(name):
    name = name.lower()
    name = re.sub('[^a-zA-Z0-9\n\.]', '', name)
    return name


def merge_plex_tautulli_movie_media_info(tautulli_media, plex_media):
    result = {
        'title': plex_media['title'],
        'rating_key': tautulli_media['rating_key'],
        'added_at': tautulli_media['added_at'],
        'last_played': tautulli_media['last_played'],
        'file_size': tautulli_media['file_size'],
        'file_name': plex_media['Media'][0]['Part'][0]['file'].rsplit('/', 1)[-1],
    }
    logging.debug('merge_plex_tautulli_movie_media_info response: ' + str(result))
    return result


def merge_plex_tautulli_show_media_info(tautulli_media, plex_media):
    result = {
        'title': plex_media['title'],
        'rating_key': plex_media['ratingKey'],
        'added_at': tautulli_media['added_at'],
        'last_played': tautulli_media['last_played'],
        'file_size': tautulli_media['file_size'],

    }
    logging.debug('merge_plex_tautulli_movie_media_info response: ' + str(result))
    return result


def merge_merged_list_radarr_media_info(merged_list, radarr_movie_list):
    logging.info('📦 Merging {} merged list and Radarr media info'.format(library['section_name']))
    merged_media_info = []

    for merged_item in merged_list:
        for radarr_item in radarr_movie_list:

            if merged_item['file_name'] == radarr_item['movieFile']['relativePath']:
                merged_item['tmdb_id'] = radarr_item['tmdbId']
                merged_item['imdb_id'] = radarr_item['imdbId']
                merged_item['radarr_id'] = radarr_item['id']
                merged_media_info.append(merged_item)
                break
    logging.info('✅ Merged {} merged list and Radarr media info'.format(library['section_name']))
    return merged_media_info


def merge_merged_list_sonarr_media_info(merged_list, sonarr_series_list):
    logging.info('📦 Merging {} merged list and Sonarr media info'.format(library['section_name']))
    merged_media_info = []
    # for merged_item in merged_list:
        # for sonarr_item in sonarr_series_list:


def filter_merged_list_based_on_remove_limit(merged_media_info):
    logging.info('📦 Filtering {} merged list based on remove limit'.format(library['section_name']))

    remove_list = []

    for media in merged_media_info:
        if media['last_played'] is None:
            date_to = datetime.datetime.fromtimestamp(int(media['added_at']))
        else:
            date_to = datetime.datetime.fromtimestamp(int(media['last_played']))

        date_from = datetime.datetime.now()

        if (date_from - date_to).days > REMOVE_LIMIT:
            remove_list.append(media)

    logging.info('✅ Filtered {} merged list based on remove limit'.format(library['section_name']))
    return remove_list


# Plex logic
parsed_plex_libraries = []
plex_libraries = get_plex_libraries()

logging.info('📦 Parsing \'get_plex_libraries\' result')

for library in plex_libraries:
    parsed_plex_libraries.append(parse_plex_library_result(library))

logging.debug('parse_plex_library_result response: ' + str(parsed_plex_libraries))
logging.info("✅ Parsed {} 'get_plex_libraries' result".format(len(plex_libraries)))

# Radarr logic
radarr_movie_list = get_radarr_movies()
radarr_movie_list = remove_radarr_movies_without_files(radarr_movie_list)

# Sonarr logic
sonarr_series_list = get_sonarr_series()

# Tautulli logic
tautulli_libraries_table = get_tautulli_libraries_table()

parsed_tautulli_libraries_table = []

logging.info("📦 Parsing 'get_tautulli_libraries_table' result")

for library in tautulli_libraries_table:
    result = parse_tautulli_libraries_table(library)
    if result is not None:
        parsed_tautulli_libraries_table.append(result)


logging.debug('parse_tautulli_libraries_table response: ' + str(parsed_tautulli_libraries_table))
logging.info("✅ Parsed {} 'get_tautulli_libraries_table' result".format(len(parsed_tautulli_libraries_table)))

for library in parsed_tautulli_libraries_table:
    tautulli_library_media_info = get_tautulli_library_media_info(library)
    plex_library_media_info = get_plex_media_info(library)
    merged_media = merge_plex_tautulli_media_info(tautulli_library_media_info, plex_library_media_info, library)

    if library['section_type'] == 'movie':
        merged_media = merge_merged_list_radarr_media_info(merged_media, radarr_movie_list)
        merged_media = filter_merged_list_based_on_remove_limit(merged_media)
        logging.info('📦 Merging {} merged list and Radarr media info'.format(library['section_name']))

    elif library['section_type'] == 'show':
        merge_merged_list_sonarr_media_info(merged_media, sonarr_series_list)



# Overseerr logic
overseerr_media_list = get_overseerr_requests()
