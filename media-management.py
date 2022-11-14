#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Delete media from server based on time last watched, or if never played based on time added based on threshold
"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import sys
import logging
from builtins import input
from builtins import object
from sys import exit

import requests
from requests import Session
from datetime import datetime
from plexapi.server import PlexServer, CONFIG
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
        logging.info('✅ Retrieved Plex libraries')
        return res_data
    except Exception as e:
        logging.error("❌ Plex API 'get_libraries' request failed: {0}".format(e))


def parse_plex_library_result(payload):
    result = {
        'library_id': payload['key'],
        'type': payload['type'],
        'name': payload['title']
    }

    return result


parsed_plex_libraries = []
plex_libraries = get_plex_libraries()

logging.info("📶 Parsing 'get_plex_libraries' result")

for library in plex_libraries:
    parsed_plex_libraries.append(parse_plex_library_result(library))

logging.debug('parse_plex_library_result response: ' + str(parsed_plex_libraries))
logging.info("✅ Parsed 'get_plex_libraries' result")

print(parsed_plex_libraries)

