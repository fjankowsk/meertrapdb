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
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
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
        choices=['heimdall', 'knownsources', 'sifting', 'timeline'],
        help='Mode of operation.'
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=__version__
    )

    return parser.parse_args()


def find_pulsars(data):
    """
    Identify pulsars by their clustering in DM.
    """

    # step size in dm
    step = 2

    dms = np.arange(np.min(data['dm']), np.max(data['dm']), step)

    dtype = [('dm',float), ('hits',int), ('snr_min',float), ('snr_med',float), ('snr_max',float)]
    info = np.zeros(len(dms), dtype=dtype)

    for i, dm in enumerate(dms):
        mask = (np.abs(data['dm'] - dm) <= step)
        sel = data[mask]

        info['dm'][i] = dm

        if len(sel) > 0:
            info['hits'][i] = len(sel)
            info['snr_min'][i] = np.min(sel['snr'])
            info['snr_med'][i] = np.median(sel['snr'])
            info['snr_max'][i] = np.max(sel['snr'])

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(info['dm'] + 1, info['hits'],
               marker='x',
               label='hits')

    ax.scatter(info['dm'] + 1, info['snr_min'],
               marker='+',
               label='min S/N')

    ax.scatter(info['dm'] + 1, info['snr_med'],
               marker='s',
               label='med S/N')

    ax.scatter(info['dm'] + 1, info['snr_max'],
               marker='d',
               label='max S/N')

    ax.grid(True)
    ax.legend(loc='best', frameon=False)
    ax.set_xscale('log', nonposx='clip')
    ax.set_yscale('log', nonposy='clip')
    ax.set_xlabel(r'DM + 1 $(\mathregular{pc} \: \mathregular{cm}^{-3})$')

    sb = data['sb'].iloc[0]
    ax.set_title('Schedule block {0}'.format(sb))

    fig.tight_layout()

    fig.savefig('find_pulsars_sb_{0}.pdf'.format(sb))
    fig.savefig('find_pulsars_sb_{0}.png'.format(sb), dpi=300)
    plt.close(fig)


def plot_heimdall(data, prefix):
    """
    Plot heimdall-like overview plot.

    Parameters
    ----------
    filename: str
        The prefix for the output file.
    """

    fig = plt.figure()
    ax = fig.add_subplot(111)

    start_time = np.min(data['mjd'])
    elapsed_time = 24 * 60 * (data['mjd'] - start_time)

    sc = ax.scatter(elapsed_time, data['dm'] + 1,
            c=data['width'],
            norm=LogNorm(),
            s=60 * data['snr'] / np.max(data['snr']),
            marker='o',
            edgecolor='black',
            lw=0.6,
            cmap='Reds',
            zorder=3
        )

    cb = plt.colorbar(sc, label='Width (ms)')

    ax.grid(True)
    ax.set_yscale('log', nonposy='clip')
    ax.set_xlabel('Time from MJD {0:.2f} (min)'.format(start_time))
    ax.set_ylabel(r'DM + 1 $(\mathregular{pc} \: \mathregular{cm}^{-3})$')
    ax.set_title('Schedule block {0}'.format(data['sb'].iloc[0]))

    # set formatting of ticklabels
    sfor = FormatStrFormatter('%g')
    ax.yaxis.set_major_formatter(sfor)
    cb.ax.yaxis.set_major_formatter(sfor)

    fig.tight_layout()

    fig.savefig('{0}.pdf'.format(prefix))
    fig.savefig('{0}.png'.format(prefix), dpi=300)
    plt.close(fig)


def run_heimdall():
    """
    Run the processing for 'heimdall' mode.
    """

    with db_session:
        temp = select(
                    (c.id, c.mjd, c.dm, c.snr, c.width,
                    beam.number, sb.sb_id, sr.is_head)
                    for c in schema.SpsCandidate
                    for beam in c.beam
                    for obs in c.observation
                    for sb in obs.schedule_block
                    for sr in c.sift_result
                    if sr.is_head == True
                ).sort_by(2)[:]

    print('Candidates loaded: {0}'.format(len(temp)))

    # convert to pandas dataframe
    temp2 = {
            'id':       [item[0] for item in temp],
            'mjd':      [item[1] for item in temp],
            'dm':       [item[2] for item in temp],
            'snr':      [item[3] for item in temp],
            'width':    [item[4] for item in temp],
            'beam':     [item[5] for item in temp],
            'sb':       [item[6] for item in temp],
            'is_head':  [item[7] for item in temp]
        }

    data = DataFrame.from_dict(temp2)

    sb_ids = np.unique(data['sb'])

    for sb_id in sb_ids:
        print('Processing schedule block: {0}'.format(sb_id))
        sel = data[data['sb'] == sb_id]

        prefix = 'heimdall_sb_{0}'.format(sb_id)
        plot_heimdall(sel, prefix)

        find_pulsars(sel)


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
    Run the processing for 'sifting' mode.
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


def plot_ks_overview(t_data):
    """
    Plot known source overview.
    """

    data = np.copy(t_data)

    fact = 1E-3

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(data['sb'], fact * data['candidates'],
               marker='x',
               s=20,
               color='black',
               label='Total')

    ax.scatter(data['sb'], fact * data['heads'],
               marker='+',
               s=20,
               color='dimgray',
               label='Cluster heads')

    ax.scatter(data['sb'], fact * data['ks'],
               marker='s',
               s=20,
               color='C0',
               label='Known sources')

    ax.scatter(data['sb'], fact * data['unique'],
               marker='*',
               s=20,
               color='C1',
               label='Unique')

    # total reduction on second axis
    ax2 = ax.twinx()

    reduction = 100 * (1.0 - data['unique'] / data['candidates'])

    ax2.scatter(data['sb'], reduction,
                marker='o',
                s=20,
                color='indianred',
                label='Total reduction')

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

    fig.savefig('ks_overview.pdf')
    fig.savefig('ks_overview.png', dpi=300)
    plt.close(fig)


def run_knownsources():
    """
    Run the processing for 'knownsources' mode.
    """

    with db_session:
        temp = select(
                    (c.id, c.mjd, c.dm, c.snr, beam.number, sb.sb_id,
                    sr.is_head, sr.members, sr.beams, len(c.known_source))
                    for c in schema.SpsCandidate
                    for beam in c.beam
                    for obs in c.observation
                    for sb in obs.schedule_block
                    for sr in c.sift_result
                ).sort_by(2)[:]

    print('Candidates loaded: {0}'.format(len(temp)))

    # convert to pandas dataframe
    temp2 = {
            'id':           [item[0] for item in temp],
            'mjd':          [item[1] for item in temp],
            'dm':           [item[2] for item in temp],
            'snr':          [item[3] for item in temp],
            'beam':         [item[4] for item in temp],
            'sb':           [item[5] for item in temp],
            'is_head':      [item[6] for item in temp],
            'members':      [item[7] for item in temp],
            'beams':        [item[8] for item in temp],
            'no_ks':        [item[9] for item in temp],
        }

    data = DataFrame.from_dict(temp2)

    sb_ids = np.unique(data['sb'])

    dtype = [('sb',int), ('candidates',int), ('heads',int), ('ks',int), ('unique',int)]
    info = np.zeros(len(sb_ids), dtype=dtype)

    for i, sb_id in enumerate(sb_ids):
        sel = data[data['sb'] == sb_id]

        mask_head = (sel['is_head'] == True)
        mask_ks = (sel['no_ks'] > 0)

        mask_unique = np.logical_and(mask_head, (sel['no_ks'] == 0))

        info[i]['sb'] = sb_id
        info[i]['candidates'] = len(sel)
        info[i]['heads'] = len(sel[mask_head])
        info[i]['ks'] = len(sel[mask_ks])
        info[i]['unique'] = len(sel[mask_unique])

    plot_ks_overview(info)


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
    Run the processing for 'timeline' mode.
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

    if args.mode == 'heimdall':
        run_heimdall()

    elif args.mode == 'knownsources':
        run_knownsources()

    elif args.mode == 'sifting':
        run_sifting()

    elif args.mode == 'timeline':
        run_timeline()

    log.info("All done.")


if __name__ == "__main__":
    main()
