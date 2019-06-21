# -*- coding: utf-8 -*-
#
#   2018 - 2019 Fabian Jankowski
#   Database related helper functions.
#

from __future__ import print_function
import logging
from pony.orm import (Database, db_session)

from config_helpers import get_config


def setup_db():
    """
    Do initial configuration of database.
    """

    config = get_config()
    dbconf = config['db']

    log = logging.getLogger('meertrapdb')
    log.info('Setting root password.')

    # set root password
    db = Database()
    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            port=dbconf['port'],
            user=dbconf['root']['name'],
            passwd='')
    
    sql = "SET PASSWORD FOR '{0}'@'{1}' = PASSWORD('{2}');".format(
        dbconf['root']['name'], dbconf['host'], dbconf['root']['password'])

    with db_session:
        db.execute(sql)
    
    db.disconnect()
    log.info('Root password was set successfully.')

    db = Database()
    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            port=dbconf['port'],
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

    log.info('Creating users and databases.')

    with db_session:
        for sql in commands:
            db.execute(sql)
            db.commit()
    
    log.info('Users and databases were created successfully.')
