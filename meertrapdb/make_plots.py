# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Generate plots from database.
#

from __future__ import print_function
import argparse
from datetime import datetime
from decimal import Decimal
import logging
import os.path
import sys
from time import sleep

from astropy.time import Time
import matplotlib.pyplot as plt
import numpy as np
from pandas import DataFrame
from pony.orm import (db_session, delete, select)

from meertrapdb.config_helpers import get_config
from meertrapdb.db_helpers import setup_db
from meertrapdb.general_helpers import setup_logging
from meertrapdb import schema
from meertrapdb.schema import db
from meertrapdb.version import __version__


def parse_args():
    parser = argparse.ArgumentParser(
        description="Make plots from database."
    )
    
    parser.add_argument(
        'mode',
        choices=['timeline'],
        help='Mode of operation.'
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=__version__
    )

    return parser.parse_args()


def run_timeline():
    """
    Run the processing for timeline mode.
    """

    with db_session:
        temp = select(
                    (c.id, c.mjd, c.dm, c.snr, beam.number, sb.sb_id)
                    for c in schema.SpsCandidate
                    for beam in c.beam
                    for obs in c.observation
                    for sb in obs.schedule_block
                ).sort_by(2)[:]

    print('Candidates loaded: {0}'.format(len(temp)))

    # convert to pandas dataframe
    temp2 = {
            'id':   [item[0] for item in temp],
            'mjd':  [item[1] for item in temp],
            'dm':   [item[2] for item in temp],
            'snr':  [item[3] for item in temp],
            'beam': [item[4] for item in temp],
            'sb':   [item[5] for item in temp]
        }

    data = DataFrame.from_dict(temp2)

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(data['mjd'], data['snr'],
              marker='x',
              color='black')

    ax.grid(True)
    #ax.legend(loc='best', frameon=False)
    ax.set_xlabel('MJD')
    ax.set_ylabel('S/N')

    fig.tight_layout()

    fig.savefig('timeline.pdf')


#
# MAIN
#

def main():
    args = parse_args()

    log = logging.getLogger('meertrapdb.make_plots')
    setup_logging()

    config = get_config()
    dbconf = config['db']

    db.bind(provider=dbconf['provider'],
            host=dbconf['host'],
            port=dbconf['port'],
            user=dbconf['user']['name'],
            passwd=dbconf['user']['password'],
            db=dbconf['database'])

    db.generate_mapping(create_tables=False)

    if args.mode == 'timeline':
        run_timeline()

    log.info("All done.")


if __name__ == "__main__":
    main()
