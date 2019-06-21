# -*- coding: utf-8 -*-
#
#   2018 - 2019 Fabian Jankowski
#   Configuration file related helper functions.
#

from __future__ import print_function
import logging
import os.path
import yaml
# local ones

# version info
__version__ = "$Revision$"

def get_config():
    """
    Load and parse a config file.

    Returns
    -------
    config : dict
        Dictionary with configuration.

    Raises
    ------
    RuntimeError:
        If `filename` does not exist.
    """

    filename = os.path.join(os.path.dirname(__file__), 'config', 'test.yml')
    filename = os.path.abspath(filename)

    log = logging.getLogger('meertrapdb')
    log.debug("Configuration file: {0}".format(filename))

    if not os.path.isfile(filename):
        raise RuntimeError("Config file does not exist: {0}".format(filename))
    
    with open(filename, 'r') as f:
        config = yaml.load(f)

    return config