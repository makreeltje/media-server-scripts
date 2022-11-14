#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Delete media from server based on time last watched, or if never played based on time added based on threshold
"""

from __future__ import print_function
from __future__ import unicode_literals

import logging

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
TAUTULLI_URL = environ.get('TAUTULLI_URL')
TAUTULLI_APIKEY = environ.get('TAUTULLI_APIKEY')

LIBRARY_NAMES = ['Movies', 'TV Shows', 'Animation', 'Series']

REMOVE_LIMIT = 30  # Days
DRY_RUN = True

headers = {
    'Accept': 'application/json'
}

logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)

# CODE BELOW #

def get_plex_libraries():
    logging.info('📶 Retrieving Plex libraries from Plex endpoint')


    payload = {
        'X-Plex-Token': PLEX_TOKEN
    }

    try:
        r = requests.get(PLEX_URL.rstrip('/') + '/library/sections/', params=payload, headers=headers)
        response = r.json()
        logging.debug('get_plex_libraries response: ' + str(response))

        res_data = response['MediaContainer']['Directory']
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


def get_radarr_movies():
    logging.info('📶 Retrieving Radarr movies from Radarr endpoint')

    payload = {
        'apikey': RADARR_APIKEY,
    }

    try:
        r = requests.get(RADARR_URL.rstrip('/') + '/api/v3/movie', params=payload)
        response = r.json()
        logging.debug('get_radarr_movies response: ' + str(response))

        logging.info('✅ Retrieved {} Radarr movies'.format(len(response)))
        return response
    except Exception as e:
        logging.error('❌ Radarr API \'movie\' request failed: {0}'.format(e))


def get_sonarr_series():
    logging.info('📶 Retrieving Sonarr series from Sonarr endpoint')

    payload = {
        'apikey': SONARR_APIKEY,
    }

    try:
        r = requests.get(SONARR_URL.rstrip('/') + '/api/v3/series', params=payload)
        response = r.json()
        logging.debug('get_sonarr_series response: ' + str(response))

        logging.info('✅ Retrieved {} Sonarr series'.format(len(response)))
        return response
    except Exception as e:
        logging.error('❌ Sonarr API \'series\' request failed: {0}'.format(e))


def get_tautulli_libraries_table():
    logging.info('📶 Retrieving Tautulli Libraries Table from Tautulli endpoint')

    payload = {
        'apikey': TAUTULLI_APIKEY,
        'cmd': 'get_libraries_table'
    }

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        logging.debug('get_tautulli_libraries_table response: ' + str(res_data))

        logging.info('✅ Retrieved {} Tautulli libraries table'.format(len(res_data)))
        return res_data
    except Exception as e:
        logging.error("❌ Tautulli API 'get_libraries_table' request failed: {0}".format(e))


def parse_tautulli_libraries_table(payload):
    result = {
        'section_name': payload['section_name'],
        'section_id': payload['section_id'],
        'rating_key': payload['rating_key'],
        'section_type': payload['section_type'],
    }

    if result['section_type'] == 'live':
        logging.warning('⚠️ Skipping live section: {}'.format(result['section_name']))
        return None
    return result


parsed_plex_libraries = []
plex_libraries = get_plex_libraries()

logging.info('📶 Parsing \'get_plex_libraries\' result')

for library in plex_libraries:
    parsed_plex_libraries.append(parse_plex_library_result(library))

logging.debug('parse_plex_library_result response: ' + str(parsed_plex_libraries))
logging.info("✅ Parsed {} 'get_plex_libraries' result".format(len(plex_libraries)))

radarr_movie_list = get_radarr_movies()
sonarr_series_list = get_sonarr_series()
tautulli_libraries_table = get_tautulli_libraries_table()

parsed_tautulli_libraries_table = []

logging.info("📶 Parsing 'get_tautulli_libraries_table' result")

for library in tautulli_libraries_table:
    result = parse_tautulli_libraries_table(library)
    if result is not None:
        parsed_tautulli_libraries_table.append(result)

logging.debug('parse_tautulli_libraries_table response: ' + str(parsed_tautulli_libraries_table))
logging.info("✅ Parsed {} 'get_tautulli_libraries_table' result".format(len(parsed_tautulli_libraries_table)))




