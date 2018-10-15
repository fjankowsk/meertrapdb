# -*- coding: utf-8 -*-
#
#   2018 Fabian Jankowski
#   Test the database.
#

from __future__ import print_function
from datetime import datetime
import logging
import signal
import sys
import pony.orm as pn
from pony.orm import db_session
# local ones
from db_helpers import setup_db
from schema import (db, Observation, BeamConfig, TuseStatus, FbfuseStatus, PeriodCandidate)

# version info
__version__ = "$Revision$"

log = logging.getLogger(__name__)

#
# MAIN
#

def main():
    setup_db()

    db.bind(provider='mysql', host='localhost', user='root', passwd='', db='test')
    db.generate_mapping(create_tables=True)

    with db_session:
        print(Observation.describe())
        Observation.select().show()

        pn.select((o.utcstart,o.cfreq,o.bw) for o in Observation).show()
    
    now = datetime.now()
    
    with db_session:
        test = Observation(ra=0,
                           dec=0,
                           mainproj="Bla",
                           proj="bdfsa",
                           observer="Fabian",
                           utcstart=now,
                           utcend=now,
                           utcadded=now,
                           finished=False,
                           nant=64,
                           cfreq=1400.123,
                           bw=800.0,
                           npol=1,
                           tsamp=0.1234)

if __name__ == "__main__":
    main()