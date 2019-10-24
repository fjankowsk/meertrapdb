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
        choices=['sifting', 'timeline'],
        help='Mode of operation.'
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=__version__
    )

    return parser.parse_args()


def plot_sift_overview(t_data):
    """
    Plot sifting overview.
    """

    data = np.copy(t_data)

    fact = 1E-3

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(data['sb'], fact * data['candidates'],
               marker='x',
               color='black',
               label='Total')

    ax.scatter(data['sb'], fact * data['heads'],
               marker='+',
               color='dimgray',
               label='Cluster heads')

    # reduction on second axis
    ax2 = ax.twinx()

    reduction = 100 * (1.0 - data['heads'] / data['candidates'])

    ax2.scatter(data['sb'], reduction,
                marker='o',
                color='indianred',
                label='Reduction')

    # median reduction
    med_red = np.median(reduction)
    ax2.axhline(y=med_red,
                color='indianred',
                lw=2,
                ls='dashed',
                label='median: {0:.1f}'.format(med_red))

    ax.grid(True)
    ax.legend(loc='upper left', frameon=False)
    ax.set_xlabel('Schedule block')
    ax.set_ylabel('Candidates (k)')

    ax2.legend(loc='upper right', frameon=False)
    ax2.set_ylim(top=100)
    ax2.set_ylabel('Reduction (per cent)')

    fig.tight_layout()

    fig.savefig('sift_overview.pdf')
    fig.savefig('sift_overview.png', dpi=300)
    plt.close(fig)


def run_sifting():
    """
    Run the processing for sifting mode.
    """

    with db_session:
        temp = select(
                    (c.id, c.mjd, c.dm, c.snr, beam.number, sb.sb_id,
                    sr.is_head, sr.members, sr.beams)
                    for c in schema.SpsCandidate
                    for beam in c.beam
                    for obs in c.observation
                    for sb in obs.schedule_block
                    for sr in c.sift_result
                ).sort_by(2)[:]

    print('Candidates loaded: {0}'.format(len(temp)))

    # convert to pandas dataframe
    temp2 = {
            'id':       [item[0] for item in temp],
            'mjd':      [item[1] for item in temp],
            'dm':       [item[2] for item in temp],
            'snr':      [item[3] for item in temp],
            'beam':     [item[4] for item in temp],
            'sb':       [item[5] for item in temp],
            'is_head':  [item[6] for item in temp],
            'members':  [item[7] for item in temp],
            'beams':    [item[8] for item in temp],
        }

    data = DataFrame.from_dict(temp2)

    sb_ids = np.unique(data['sb'])

    dtype = [('sb',int), ('candidates',int), ('heads',int)]
    info = np.zeros(len(sb_ids), dtype=dtype)

    for i, sb_id in enumerate(sb_ids):
        sel = data[data['sb'] == sb_id]

        mask = (sel['is_head'] == True)

        info[i]['sb'] = sb_id
        info[i]['candidates'] = len(sel)
        info[i]['heads'] = len(sel[mask])

    plot_sift_overview(info)


def plot_snr_timeline(data, prefix):
    """
    Plot S/N versus time.

    Parameters
    ----------
    filename: str
        The prefix for the output file.
    """

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(data['mjd'], data['snr'] + 1,
               marker='x',
               color='black')

    ax.grid(True)
    #ax.legend(loc='best', frameon=False)
    ax.set_yscale('log', nonposy='clip')
    ax.set_xlabel('MJD')
    ax.set_ylabel('S/N + 1')

    fig.tight_layout()

    fig.savefig('{0}.pdf'.format(prefix))
    fig.savefig('{0}.png'.format(prefix), dpi=300)
    plt.close(fig)


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

    # total timeline
    plot_snr_timeline(data, 'timeline_total')

    # timeline by schedule block
    sb_ids = np.unique(data['sb'])

    for sb_id in sb_ids:
        sel = data[data['sb'] == sb_id]

        prefix = 'timeline_sb_{0}'.format(sb_id)
        plot_snr_timeline(sel, prefix)


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

    if args.mode == 'sifting':
        run_sifting()

    elif args.mode == 'timeline':
        run_timeline()

    log.info("All done.")


if __name__ == "__main__":
    main()
