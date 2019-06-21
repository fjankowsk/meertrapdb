# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Populate the database.
#

from __future__ import print_function
import argparse
import logging

from config_helpers import get_config
from db_helpers import setup_db
from db_logger import  DBHandler
from general_helpers import setup_logging
from schema import db
from version import __version__


def parse_args():
    parser = argparse.ArgumentParser(
        description="Populate the database.")
    
    parser.add_argument(
        "--version",
        action="version",
        version=__version__)

    return parser.parse_args()


#
# MAIN
#

def main():
    parse_args()

    log = logging.getLogger('meertrapdb')
    setup_logging()

    config = get_config()
    dbconf = config['db']

    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            port=dbconf['port'],
            user=dbconf['user']['name'],
            passwd=dbconf['user']['password'],
            db=dbconf['database'])

    db.generate_mapping(create_tables=True)
    
    log.info("All done.")


if __name__ == "__main__":
    main()
