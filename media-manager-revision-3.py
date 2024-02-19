import logging
import os
from typing import Any

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

DRY_RUN = False
PLEX_LIBRARY_NAMES = ['Series', 'Movies', 'Animation', 'TV Shows']
PATH_TO_CHECK = '/data'
SERVICE_TO_CHECK_FREE_DISKSPACE = 'sonarr'  # sonarr/radarr
FREE_SPACE_THRESHOLD = 500  # Threshold in GB

logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)

DIFFERENCE_IN_FREESPACE_AND_THRESHOLD = 0


def setup_server(url, token):
    return PlexServer(url, token)


def get_plex_libraries_metadata(plex, library_name):
    return plex.library.section(library_name).all()


def get_full_plex_history(plex, rating_key):
    return plex.history(maxresults=1, ratingKey=rating_key)


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


def get_external_ids(library_item):
    guids_dict = {}
    for guid in library_item.guids:
        parts = guid.id.split('://')
        if len(parts) == 2:
            key = parts[0]
            value = parts[1]
            guids_dict[key] = value

    key_mapping = {'imdb': 'imdbId', 'tmdb': 'tmdbId', 'tvdb': 'tvdbId'}

    # Create a new dictionary with modified keys
    modified_guids_dict = {key_mapping.get(k, k): v for k, v in guids_dict.items()}

    return modified_guids_dict


def check_diskspace(path, service, freespace_threshold):
    if SERVICE_TO_CHECK_FREE_DISKSPACE == 'sonarr':
        free_diskspace = check_sonarr_free_diskspace(path)
    elif SERVICE_TO_CHECK_FREE_DISKSPACE == 'radarr':
        free_diskspace = check_radarr_free_diskspace(path)

    if free_diskspace < freespace_threshold * 1073741824:
        global space_to_clear
        logging.info('💾 The directory {} in {} has {} free space, '
                     'this is below the set threshold of {} GB. Running cleanup'
                     .format(path, service, sizeof_fmt(free_diskspace), freespace_threshold))
        space_to_clear = free_diskspace - freespace_threshold
        return True
    logging.info(
        '💾 The directory {} in {} has {} free space, '
        'this is above the set threshold of {} GB. Skipping cleanup'
        .format(path, service, sizeof_fmt(free_diskspace), freespace_threshold))
    return False


def get_radarr_movies():
    logging.info('📦 Retrieving Radarr movies')

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


def delete_radarr_movie(movie):
    logging.info('📦 Deleting Radarr movie {}'.format(movie['title']))

    payload = {
        'apikey': RADARR_APIKEY,
        'deleteFiles': True
    }

    try:
        r = requests.delete(RADARR_URL.rstrip('/') + '/api/v3/movie/{}'.format(movie['id']), params=payload)
        response = r.json()
        logging.debug('delete_radarr_movie response: ' + str(response))

        if r.status_code != 200:
            logging.warning('🚧 No Radarr show found')
        else:
            logging.info('✅ Deleted {} Radarr movie'.format(movie['title']))

        return response
    except Exception as e:
        logging.error('❌ Radarr API \'movie\' request failed: {0}'.format(e))


def get_sonarr_shows():
    logging.info('📦 Retrieving Sonarr shows')

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


def delete_sonarr_show(show):
    logging.info('📦 Deleting Sonarr show {}'.format(show['title']))

    payload = {
        'apikey': SONARR_APIKEY,
        'deleteFiles': True
    }

    try:
        r = requests.delete(SONARR_URL.rstrip('/') + '/api/v3/series/{}'.format(show['id']), params=payload)
        response = r.json()
        logging.debug('delete_sonarr_show response: ' + str(response))

        if r.status_code != 200:
            logging.warning('🚧 No Sonarr show found')
        else:
            logging.info('✅ Deleted {} Sonarr show'.format(show['title']))

        return response
    except Exception as e:
        logging.error('❌ Sonarr API \'series\' request failed: {0}'.format(e))


def get_id_type(item):
    if 'imdbId' in item:
        return 'imdbId'
    elif 'tmdbId' in item:
        return 'tmdbId'
    elif 'tvdbId' in item:
        return 'tvdbId'
    else:
        return None


def find_matching_item(library_item, library_type, library):
    external_ids = get_external_ids(library_item)
    id_type = None

    for item in library:
        id_type = get_id_type(item)
        if external_ids.get(id_type) == item.get(id_type):
            return item, id_type

    return None, id_type


def start():
    plex = setup_server(PLEX_URL, PLEX_TOKEN)
    full_library_metadata: list[Any] = []
    for library_name in PLEX_LIBRARY_NAMES:
        full_library_metadata.extend(get_plex_libraries_metadata(plex, library_name))
    for item in full_library_metadata:
        history = get_full_plex_history(plex, item.ratingKey)
        if len(history) > 0:
            if item.addedAt > history[0].viewedAt:
                item.lastViewedAt = item.addedAt
            else:
                item.lastViewedAt = history[0].viewedAt
        else:
            item.lastViewedAt = item.addedAt
    sorted_full_library_metadata = sorted(full_library_metadata, key=sort_library_metadata, reverse=False)

    radarr_library = get_radarr_movies()
    sonarr_library = get_sonarr_shows()

    deleted_bytes = 0
    free_diskspace = 0

    if SERVICE_TO_CHECK_FREE_DISKSPACE == 'sonarr':
        free_diskspace = check_sonarr_free_diskspace(PATH_TO_CHECK)
    elif SERVICE_TO_CHECK_FREE_DISKSPACE == 'radarr':
        free_diskspace = check_radarr_free_diskspace(PATH_TO_CHECK)

    bytes_to_delete = (FREE_SPACE_THRESHOLD * 1073741824) - free_diskspace

    if DRY_RUN:
        logging.info("The following items should be deleted to be back at the set {} GB diskspace:".format(FREE_SPACE_THRESHOLD))
    else:
        logging.info("Deleting items from Radarr/Sonarr till free diskspace is at least {} GB".format(FREE_SPACE_THRESHOLD))

    for library_item in sorted_full_library_metadata:
        if library_item.type == 'movie':
            matching_movie, id_type = find_matching_item(library_item, 'movie', radarr_library)
            if matching_movie:
                if not DRY_RUN:
                    delete_radarr_movie(matching_movie)
                else:
                    logging.info("Movie: {}".format(matching_movie['title']))
                deleted_bytes += matching_movie['sizeOnDisk']
        else:  # Assuming 'show' type
            matching_show, id_type = find_matching_item(library_item, 'show', sonarr_library)
            if matching_show:
                if not DRY_RUN:
                    delete_sonarr_show(matching_show)
                else:
                    logging.info("Show: {} ".format(matching_show['title']))
                deleted_bytes += matching_show['statistics']['sizeOnDisk']
        if deleted_bytes > bytes_to_delete:
            break

    if DRY_RUN:
        logging.info("Listted a total of {}".format(sizeof_fmt(deleted_bytes)))
    else:
        logging.info("Deleted a total of {}".format(sizeof_fmt(deleted_bytes)))


run_cleanup = check_diskspace(PATH_TO_CHECK, SERVICE_TO_CHECK_FREE_DISKSPACE, FREE_SPACE_THRESHOLD)

if run_cleanup:
    start()
