# -*- coding: utf-8 -*-
#
#   2019 - 2020 Fabian Jankowski
#   Schedule block related helper functions.
#

import os.path
import json

from meertrapdb.config_helpers import get_config


def get_sb_info(version):
    """
    Load the schedule block information from file.

    Parameters
    ----------
    version: int
        Version 1: read the schedule block parameters from a quasi-static JSON file
        that ships with meertrapdb.
        Version 2: read the SB parameters from a new style JSON file in each
        observing directory.

    Returns
    -------
    data: dict
        The schedule block information.

    Raises
    ------
    RuntimeError
        In case of problems.
    """

    config = get_config()
    fsconf = config['filesystem']

    sb_info_file = os.path.join(
        os.path.dirname(__file__),
        'config',
        fsconf['sb_info']['filename']
    )

    if not os.path.isfile(sb_info_file):
        raise RuntimeError('SB info file does not exist: {0}'.format(sb_info_file))

    with open(sb_info_file, 'r') as fh:
        data = json.load(fh)

    return data
