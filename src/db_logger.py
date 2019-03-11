# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Log to database.
#

from __future__ import print_function
from datetime import datetime
import logging
from pony.orm import db_session
# local ones
from schema import Logs

# version info
__version__ = "$Revision$"


class DBHandler(logging.Handler):
    def emit(self, record):
        with db_session:
            Logs(
                utc=datetime.fromtimestamp(record.created),
                program="{!s}".format(record.filename),
                process="{!s}".format(record.processName),
                logger="{!s}".format(record.name),
                module="{!s}".format(record.module),
                level=record.levelno,
                message="{!s}".format(record.msg)
            )