#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Delete media from server based on time last watched, or if never played based on time added based on threshold

"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import time
from dotenv import load_dotenv
# import shutil


# from builtins import input
# from builtins import object
# from sys import exit

import requests

# from requests import Session
# from datetime import datetime
# from plexapi.server import PlexServer, CONFIG

load_dotenv(dotenv_path='./.env')

# EDIT PARAMETERS IN .env FILE #

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
RADARR_URL = os.getenv('RADARR_URL')
RADARR_APIKEY = os.getenv('RADARR_APIKEY')
SONARR_URL = os.getenv('SONARR_URL')
SONARR_APIKEY = os.getenv('SONARR_APIKEY')
TAUTULLI_URL = os.getenv('TAUTULLI_URL')
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY')

LIBRARY_NAMES = ['Movies', 'TV Shows', 'Animation', 'Series']

REMOVE_LIMIT = 30  # Days
DRY_RUN = True


# CODE BELOW #

def get_radarr_movies():
    payload = {
        'apikey': RADARR_APIKEY
    }

    try:
        r = requests.get(RADARR_URL.rstrip('/') + '/api/v3/movie', params=payload)
        response = r.json()

        return response
    except Exception as e:
        sys.stderr.write("Radarr API 'get_radarr_movies' request failed: {0}".format(e))


def get_sonarr_series():
    payload = {
        'apikey': SONARR_APIKEY
    }

    try:
        r = requests.get(SONARR_URL.rstrip('/') + '/api/v3/series', params=payload)
        response = r.json()

        return response
    except Exception as e:
        sys.stderr.write("Sonarr API 'get_sonarr_series' request failed: {0}".format(e))


def get_sonarr_episodes(seriesId, seasonNumber):
    payload = {
        'apikey': SONARR_APIKEY,
        'seriesId': seriesId,
        'seasonNumber': seasonNumber
    }

    try:
        r = requests.get(SONARR_URL.rstrip('/') + '/api/v3/episode', params=payload)
        response = r.json()

        return response
    except Exception as e:
        sys.stderr.write("Sonarr API 'get_sonarr_episode' request failed: {0}".format(e))

def get_tautulli_history(start):
    payload = {
        'apikey': TAUTULLI_APIKEY,
        # 'rating_key': rating_key,
        'cmd': 'get_history',
        'start': start,
        'length': 25
    }

    try:
        r = requests.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=payload)
        response = r.json()

        res_data = response['response']['data']['data']
        return res_data
    except Exception as e:
        sys.stderr.write("Tautulli API 'get_tautulli_history' request failed: {0}".format(e))


print(get_sonarr_episodes(2,1))
time.sleep(5)