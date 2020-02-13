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

from astropy import units
from astropy.coordinates import SkyCoord
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

# astropy.units generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def parse_args():
    parser = argparse.ArgumentParser(
        description="Make plots from database."
    )
    
    parser.add_argument(
        'mode',
        choices=['heimdall', 'knownsources', 'sifting', 'timeline', 'skymap'],
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
               label='Total',
               zorder=2)

    ax.scatter(data['sb'], fact * data['heads'],
               marker='+',
               s=20,
               color='dimgray',
               label='Cluster heads',
               zorder=3)

    ax.scatter(data['sb'], fact * data['ks'],
               marker='s',
               s=20,
               color='C0',
               label='Known sources',
               zorder=4)

    ax.scatter(data['sb'], fact * data['unique'],
               marker='*',
               s=20,
               color='C1',
               label='Unique',
               zorder=5)

    # total reduction on second axis
    ax2 = ax.twinx()

    reduction = 100 * (1.0 - data['unique'] / data['candidates'])

    ax2.scatter(data['sb'], reduction,
                marker='o',
                s=20,
                color='indianred',
                label='Total reduction',
                zorder=6)

    # median reduction
    med_red = np.median(reduction)
    ax2.axhline(y=med_red,
                color='indianred',
                lw=2,
                ls='dashed',
                label='median: {0:.1f}'.format(med_red),
                zorder=5)

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


def run_skymap():
    """
    Run the processing for 'skymap' mode.
    """

    with db_session:
        temp = select(
                (b.id, b.number, b.ra, b.dec, b.coherent,
                 obs.nant, obs.utc_start, obs.utc_end)
                    for c in schema.SpsCandidate
                    for b in c.beam
                    for obs in c.observation
                ).sort_by(7)[:]

    print('Beams loaded: {0}'.format(len(temp)))

    # convert to pandas dataframe
    temp2 = {
            'id':           [item[0] for item in temp],
            'number':       [item[1] for item in temp],
            'ra':           [item[2] for item in temp],
            'dec':          [item[3] for item in temp],
            'coherent':     [item[4] for item in temp],
            'nant':         [item[5] for item in temp],
            'utc_start':    [item[6] for item in temp],
            'utc_end':      [item[7] for item in temp]
        }

    data = DataFrame.from_dict(temp2)

    # assume contant tobs (hr) for now
    tobs = 10.0 / 60.0
    data['tobs'] = tobs

    # galactic latitude thresholds
    lat_thresh = [5, 10, 15, 45, 90]

    # split into coherent and incoherent beams
    coherent = data[data['number'] != 0].copy()
    inco = data[data['number'] == 0].copy()

    coords_co = SkyCoord(
        ra=coherent['ra'],
        dec=coherent['dec'],
        unit=(units.hourangle, units.deg),
        frame='icrs'
    )

    coords_in = SkyCoord(
        ra=inco['ra'],
        dec=inco['dec'],
        unit=(units.hourangle, units.deg),
        frame='icrs'
    )

    # 1) coherent search
    print('Coherent search:')

    # assume constant tied-array beam area (deg2) for now
    a = 28.8 / 3600
    b = 64.0 / 3600
    # about 1.6 arcmin2, or 0.44 mdeg2
    area_co = np.pi * a * b

    plot_skymap_equatorial(coords_co, coherent, 'coherent', 300)
    plot_skymap_galactic(coords_co, coherent, 'coherent', 300)

    # do analysis by galactic latitude bins
    for i in range(len(lat_thresh) - 1):
        start = lat_thresh[i]
        stop = lat_thresh[i + 1]
        print('Latitude range: +- [{0}, {1}[ deg'.format(start, stop))

        mask_co = np.logical_and(
            start <= np.abs(coords_co.galactic.b.deg),
            np.abs(coords_co.galactic.b.deg) < stop
        )

        mask_in = np.logical_and(
            start <= np.abs(coords_in.galactic.b.deg),
            np.abs(coords_in.galactic.b.deg) < stop
        )

        nbeams = len(coherent[mask_co]) + 0.5 * len(inco[mask_in])
        print('Total area: {0:.2f} deg2'.format(nbeams * area_co))
        print('Total time: {0:.2f} beam hr'.format(nbeams * tobs))
        print('Total coverage: {0:.2f} hr deg2'.format(nbeams * area_co * tobs))

    # 2) incoherent search
    print('Incoherent search:')

    # area of the primary beam (deg2) at 1284 MHz
    area_inco = 0.97

    plot_skymap_equatorial(coords_in, inco, 'inco', 150)
    plot_skymap_galactic(coords_in, inco, 'inco', 150)

    # do analysis by galactic latitude bins
    for i in range(len(lat_thresh) - 1):
        start = lat_thresh[i]
        stop = lat_thresh[i + 1]
        print('Latitude range: +- [{0}, {1}[ deg'.format(start, stop))

        mask_in = np.logical_and(
            start <= np.abs(coords_in.galactic.b.deg),
            np.abs(coords_in.galactic.b.deg) < stop
        )

        nbeams = 0.5 * len(inco[mask_in])

        print('Total area: {0:.2f} deg2'.format(nbeams * area_inco))
        print('Total time: {0:.2f} beam hr'.format(nbeams * tobs))
        print('Total coverage: {0:.2f} hr deg2'.format(nbeams * area_inco * tobs))


def get_area_polygon(x, y):
    """
    Compute the area of a polygon using the shoelace formula.

    Parameters
    ----------
    x: ~np.array
        The horizontal Euclidian coordinates of the polygon corners.
    y: ~np.array
        The vertical Euclidian coordinates of the polygon corners.
    """

    area = 0.5 * np.abs(
        np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1))
    )

    return area


def plot_skymap_equatorial(coords, data, suffix, gridsize):
    """
    Plot a sky map in equatorial coordinates.

    Parameters
    ----------
    coords: ~astropy.SkyCoord
        The coordinates of the beam pointings.
    data: ~pandas.Dataframe
        The data to be plotted.
    suffix: str
        The suffix to append to the filename of the output plot.
    gridsize: int
        The number of hexagons in the horizontal direction.
    """

    fig = plt.figure()
    ax = fig.add_subplot(111)

    hb = ax.hexbin(coords.ra.hour, coords.dec.degree,
                   C=data['tobs'],
                   reduce_C_function=np.sum,
                   gridsize=gridsize,
                   bins='log',
                   mincnt=1,
                   linewidths=0.1,
                   cmap='Reds')

    # get unique area from the number of filled hexagons
    counts = hb.get_array()
    corners = hb.get_paths()

    # get the area of one hexagon
    xv = np.array([item[0][0] for item in corners[0].iter_segments()])
    yv = np.array([item[0][1] for item in corners[0].iter_segments()])
    area_hexagon = get_area_polygon(xv, yv)
    print('Area hexagon: {0:.5f}'.format(area_hexagon))

    filled = counts[counts > 0]
    print('Number of hexagons: {0}'.format(len(counts)))
    print('Number of filled hexagons: {0}'.format(len(filled)))
    print('Unique area: {0:.2f} deg2'.format(len(filled) * area_hexagon * 15.0))

    # add colour bar
    cb = fig.colorbar(hb, ax=ax)
    cb.set_label('Exposure (hr)')

    ax.grid(True)
    ax.set_xlabel("RA (h)")
    ax.set_ylabel("Dec (deg)")
    #ax.autoscale(tight=True)
    ax.set_xlim(left=0, right=24)

    fig.tight_layout()

    fig.savefig('skymap_equatorial_{0}.pdf'.format(suffix), bbox_inches='tight')
    fig.savefig('skymap_equatorial_{0}.png'.format(suffix), bbox_inches='tight', dpi=300)
    plt.close(fig)


def plot_skymap_galactic(coords, data, suffix, gridsize):
    """
    Plot a sky map in Galactic coordinates.

    Parameters
    ----------
    coords: ~astropy.SkyCoord
        The coordinates of the beam pointings.
    data: ~pandas.Dataframe
        The data to be plotted.
    suffix: str
        The suffix to append to the filename of the output plot.
    gridsize: int
        The number of hexagons in the horizontal direction.
    """

    fig = plt.figure(figsize=(8, 4.2))
    ax = fig.add_subplot(111, projection='aitoff')

    gl_rad = coords.galactic.l.wrap_at(180 * units.deg).radian
    gb_rad = coords.galactic.b.radian

    hb = ax.hexbin(-1 * gl_rad, gb_rad,
                   C=data['tobs'],
                   reduce_C_function=np.sum,
                   gridsize=gridsize,
                   bins='log',
                   mincnt=1,
                   linewidths=0.3,
                   cmap='Reds')

    # add colour bar
    cb = fig.colorbar(hb, ax=ax)
    cb.set_label('Exposure (hr)')

    ax.grid(True)
    ax.set_xlabel("Galactic Longitude (deg)")
    ax.set_ylabel("Galactic Latitude (deg)")

    # flip gb axis labels
    labels = ['{0:.0f}'.format(item) for item in np.linspace(150, -150, num=11)]
    ax.set_xticklabels(labels)

    fig.tight_layout()
    fig.savefig('skymap_galactic_{0}.pdf'.format(suffix), bbox_inches="tight")
    fig.savefig('skymap_galactic_{0}.png'.format(suffix), bbox_inches="tight", dpi=300)
    plt.close(fig)


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

    elif args.mode == 'skymap':
        run_skymap()

    log.info("All done.")


if __name__ == "__main__":
    main()
