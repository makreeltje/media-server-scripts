#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Delete media from server based on time last watched, or if never played based on time added based on threshold
"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
import sys
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


# CODE BELOW #

def get_plex_libraries():
    payload = {
        'X-Plex-Token': PLEX_TOKEN
    }

    try:
        r = requests.get(PLEX_URL.rstrip('/') + '/library/sections/', params=payload, headers=headers)
        response = r.json()

        res_data = response['MediaContainer']['Directory']
        return res_data
    except Exception as e:
        sys.stderr.write("\N{cross mark} Plex API 'get_libraries' request failed: {0}".format(e))
        pass


def parse_plex_library_result(payload):
    result = {
        'library_id': payload['key'],
        'type': payload['type'],
        'name': payload['title']
    }

    return result


def get_metadata(rating_key):
    payload = {'apikey': TAUTULLI_APIKEY,
               'cmd': 'get_metadata',
               'rating_key': rating_key,
               'media_info': True}

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']
        print(res_data)
    except Exception as e:
        sys.stderr.write("Tautulli API 'get_metadata' request failed: {0}.".format(e))
        pass


print("Plex data")
print("URL  : " + str(PLEX_URL))
print("TOKEN: " + str(PLEX_TOKEN))

plex_libraries = get_plex_libraries()

for library in plex_libraries:
    print(parse_plex_library_result(library))

