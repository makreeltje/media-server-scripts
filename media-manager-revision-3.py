import logging
import os
from typing import List, Any

import requests
from dotenv import load_dotenv
from plexapi.server import PlexServer

load_dotenv()

# EDIT PARAMETERS IN .env FILE #
PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
RADARR_URL = os.getenv('RADARR_URL')
RADARR_APIKEY = os.getenv('RADARR_APIKEY')
SONARR_URL = os.getenv('SONARR_URL')
SONARR_APIKEY = os.getenv('SONARR_APIKEY')
OVERSEERR_URL = os.getenv('OVERSEERR_URL')
OVERSEERR_APIKEY = os.getenv('OVERSEERR_APIKEY')
TAUTULLI_URL = os.getenv('TAUTULLI_URL')
TAUTULLI_APIKEY = os.getenv('TAUTULLI_APIKEY')

DRY_RUN = True
PLEX_LIBRARY_NAMES = ['Movies', 'TV Shows', 'Animation', 'Series']
PATH_TO_CHECK = '/data'
SERVICE_TO_CHECK_FREE_DISKSPACE = 'sonarr' # sonarr/radarr
FREE_SPACE_THRESHOLD = 200 # Threshold in GB

logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)


def setup_server(url, token):
    return PlexServer(url, token)


def get_plex_libraries_metadata(plex, library_name):
    return plex.library.section(library_name).all()


def sort_library_metadata(library_metadata):
    if library_metadata.lastViewedAt:
        return library_metadata.lastViewedAt
    else:
        return library_metadata.addedAt


def check_radarr_free_diskspace(path):
    logging.info('📦 Retrieving disk(s) information from Radarr')

    payload = {
        'apikey': RADARR_APIKEY,
    }

    try:
        r = requests.get(RADARR_URL.rstrip('/') + '/api/v3/diskspace', params=payload)
        response = r.json()
        logging.debug('get_radarr_diskspace response: ' + str(response))

        if len(response) == 0:
            logging.warning('🚧 No Radarr disk(s) found')
        else:
            logging.info('✅ Retrieved {} Radarr disk(s)'.format(len(response)))

        return get_freespace_on_specified_path(response, path)
    except Exception as e:
        logging.error('❌ Radarr API \'diskspace\' request failed: {0}'.format(e))


def check_sonarr_free_diskspace(path):
    logging.info('📦 Retrieving disk(s) information from Sonarr')

    payload = {
        'apikey': SONARR_APIKEY,
    }

    try:
        r = requests.get(SONARR_URL.rstrip('/') + '/api/v3/diskspace', params=payload)
        response = r.json()
        logging.debug('get_sonarr_diskspace response: ' + str(response))

        if len(response) == 0:
            logging.warning('🚧 No Sonarr disk(s) found')
        else:
            logging.info('✅ Retrieved {} Sonarr disk(s)'.format(len(response)))
        return get_freespace_on_specified_path(response, path)
    except Exception as e:
        logging.error('❌ Sonarr API \'diskspace\' request failed: {0}'.format(e))


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def get_freespace_on_specified_path(data, path):
    for object in data:
        if object['path'] == path:
            return object['freeSpace']


def start():

    plex = setup_server(PLEX_URL, PLEX_TOKEN)
    full_library_metadata: list[Any] = []
    for library_name in PLEX_LIBRARY_NAMES:
        full_library_metadata.extend(get_plex_libraries_metadata(plex, library_name))
    sorted_full_library_metadata = sorted(full_library_metadata, key=sort_library_metadata, reverse=False)
    for library_item in sorted_full_library_metadata:
        guids_str = ' '.join(
            [guid.id.split('//')[1][:-1] for guid in library_item.guids]) if library_item.guids else "N/A"
        if library_item.lastViewedAt is not None:
            print(f"{library_item.lastViewedAt}, LVA, {guids_str}")
        else:
            print(f"{library_item.addedAt}, AA, {guids_str}")
    print('pannenkoek')


def check_diskspace(path, service, freespace_threshold):
    if SERVICE_TO_CHECK_FREE_DISKSPACE == 'sonarr':
        free_diskspace = check_sonarr_free_diskspace(path)
    elif SERVICE_TO_CHECK_FREE_DISKSPACE == 'radarr':
        free_diskspace = check_radarr_free_diskspace(path)

    if free_diskspace < freespace_threshold * 1073741824:
        logging.info('💾 The directory {} in {} has {} free space, '
                     'this is below the set threshold of {} GB. Running cleanup'
                     .format(path, service,sizeof_fmt(free_diskspace), freespace_threshold))
        return True
    logging.info(
        '💾 The directory {} in {} has {} free space, '
        'this is above the set threshold of {} GB. Skipping cleanup'
        .format(path, service, sizeof_fmt(free_diskspace), freespace_threshold))
    return False


run_cleanup = check_diskspace(PATH_TO_CHECK, SERVICE_TO_CHECK_FREE_DISKSPACE, FREE_SPACE_THRESHOLD)

if run_cleanup:
    start()
