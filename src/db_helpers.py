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

# version info
__version__ = "$Revision$"

log = logging.getLogger(__name__)

def setup_db():
    """
    Do initial configuration of database.
    """

    db = Database()
    db.bind(provider='mysql', host='localhost', user='root', passwd='')

    commands = [
        "CREATE USER IF NOT EXISTS meertrap@localhost IDENTIFIED BY 'password1';",
        "CREATE USER IF NOT EXISTS meertrap_ro@localhost IDENTIFIED BY 'password2';",
        "CREATE DATABASE IF NOT EXISTS test;"
    ]

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

    db = Database()
    db.bind(provider='mysql', host='localhost', user='root', passwd='')
    
    with db_session:
        for sql in commands:
            db.execute(sql)
            db.commit()
