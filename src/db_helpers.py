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

def signal_handler(signum, frame):
    """
    Handle UNIX signals sent to the program.
    """

    # treat SIGINT/INT/CRTL-C
    if signum == signal.SIGINT:
        log.warn("SIGINT received, stopping the program.")
        sys.exit(1)


def setup_db():
    """
    Do initial configuration of database.
    """
    
    db = Database()
    db.bind(provider='mysql', host='localhost', user='root', passwd='')

    sql = """CREATE USER meertrap@localhost IDENTIFIED BY 'password';
    CREATE DATABASE test;
    """
    
    with db_session:
        cursor = db.execute(sql)



def init_tables():
    """
    Initialise the database tables.
    """

    pass