# -*- coding: utf-8 -*-
#
#   2018 Fabian Jankowski
#   Database related helper functions.
#

from __future__ import print_function
import logging
import signal
import sys
from pony.orm import (Database, db_session)
# local ones
from config_helpers import get_config

# version info
__version__ = "$Revision$"

log = logging.getLogger(__name__)

def setup_db():
    """
    Do initial configuration of database.
    """

    config = get_config()
    dbconf = config['db']

    # set root password
    db = Database()
    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            user=dbconf['root']['name'],
            passwd='')
    
    sql = "SET PASSWORD FOR '{0}'@'{1}' = PASSWORD('{2}');".format(
        dbconf['root']['name'], dbconf['host'], dbconf['root']['password'])

    with db_session:
        db.execute(sql)
    
    db.disconnect()

    db = Database()
    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            user=dbconf['root']['name'],
            passwd=dbconf['root']['password'])

    commands = []

    for user in dbconf['users']:
        command = "CREATE USER IF NOT EXISTS '{0}'@'{1}' IDENTIFIED BY '{2}';".format(
            user['name'], dbconf['host'], user['password']
        )
        commands.append(command)
    
    for database in dbconf['databases']:
        command = "CREATE DATABASE IF NOT EXISTS {0};".format(database['name'])
        commands.append(command)

    with db_session:
        for sql in commands:
            db.execute(sql)
            db.commit()


def init_tables():
    """
    Initialise the database tables.
    """

    filename = "schema.sql"

    with open(filename) as f:
        raw = f.read()

    commands = raw.split(";")

    # remove empty last item
    commands = commands[:-1]

    config = get_config()
    dbconf = config['db']

    db = Database()
    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            user=dbconf['root']['name'],
            passwd=dbconf['root']['password'])

    with db_session:
        for sql in commands:
            db.execute(sql)
            db.commit()
