"""Data set registry."""
import datetime
import glob
import json
import os

import humanize
import logbook

log = logbook.Logger(__name__)


def get_data_sets():
    """List of available data sets."""
    ds_info = {}
    for path in glob.glob('data/*.json'):
        try:
            name = os.path.split(path)[1].split('.json')[0]
        except IndexError as e:
            log.error(f'Failed to determine data set name: {e}')
            continue
        else:
            ds_info[name] = _summary(path)
    return ds_info


def get_data_set_content(path):
    """Get data set content.

    Given a path, get data set content.  The content is expected to be a simple
    list of words or phrases.

    :param (str) path: Path to data set file.
    :returns (list): The list of words or phrases, otherwise an empty list.
    """
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        log.error(f'Failed to get data set content for {path}')
        return []


def _summary(path):
    """Data set summary info.

    :param (str) path: Path to data set.
    :returns (dict): Data set summary or an error.
    """
    try:
        status = os.stat(path)
    except (FileNotFoundError, OSError):
        return {'error': 'Cannot status data'}
    else:
        dts = datetime.datetime.utcfromtimestamp(status.st_mtime).isoformat()
        size = humanize.naturalsize(status.st_size)
        return {'source': path,
                'size_bytes': status.st_size,
                'size': size,
                'timestamp_raw': status.st_mtime,
                'timestamp': dts,
                'item_count': _item_count(path)
                }


def _item_count(path):
    """The number of items in a data set.

    :param (str) path: Path to data set.
    :returns (int): Item count or zero if json could not be decoded.
    """
    try:
        with open(path, 'r') as f:
            return len(json.load(f))
    except json.JSONDecodeError:
        log.error(f'Failed to determine number of data set items for {path}')
        return 0
