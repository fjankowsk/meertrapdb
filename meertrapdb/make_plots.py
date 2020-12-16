# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Generate plots from database.
#

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
import pandas as pd
from pandas import DataFrame
from pony.orm import (db_session, delete, select)

from meertrapdb.config_helpers import get_config
from meertrapdb.db_helpers import setup_db
from meertrapdb.general_helpers import setup_logging
from meertrapdb import schema
from meertrapdb.schema import db
from meertrapdb.skymap import Skymap
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
        choices=[
            'heimdall',
            'knownsources',
            'sifting',
            'skymap',
            'timeline',
            'timeonsky'
        ],
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

    dtype = [
        ('dm',float), ('hits',int),
        ('snr_min',float), ('snr_med',float), ('snr_max',float)
    ]
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

    ax.scatter(
        info['dm'] + 1,
        info['hits'],
        marker='x',
        label='hits'
    )

    ax.scatter(
        info['dm'] + 1,
        info['snr_min'],
        marker='+',
        label='min S/N'
    )

    ax.scatter(
        info['dm'] + 1,
        info['snr_med'],
        marker='s',
        label='med S/N'
    )

    ax.scatter(
        info['dm'] + 1,
        info['snr_max'],
        marker='d',
        label='max S/N'
    )

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

    sc = ax.scatter(
        elapsed_time,
        data['dm'] + 1,
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

    ax.scatter(
        data['sb'],
        fact * data['candidates'],
        marker='x',
        color='black',
        label='Total'
    )

    ax.scatter(
        data['sb'],
        fact * data['heads'],
        marker='+',
        color='dimgray',
        label='Cluster heads'
    )

    # reduction on second axis
    ax2 = ax.twinx()

    reduction = 100 * (1.0 - data['heads'] / data['candidates'])

    ax2.scatter(
        data['sb'], reduction,
        marker='o',
        color='indianred',
        label='Reduction'
    )

    # median reduction
    med_red = np.median(reduction)
    ax2.axhline(
        y=med_red,
        color='indianred',
        lw=2,
        ls='dashed',
        label='median: {0:.1f}'.format(med_red)
    )

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

    ax.scatter(
        data['sb'],
        fact * data['candidates'],
        marker='x',
        s=20,
        color='black',
        label='Total',
        zorder=2
    )

    ax.scatter(
        data['sb'],
        fact * data['heads'],
        marker='+',
        s=20,
        color='dimgray',
        label='Cluster heads',
        zorder=3
    )

    ax.scatter(
        data['sb'], fact * data['ks'],
        marker='s',
        s=20,
        color='C0',
        label='Known sources',
        zorder=4
    )

    ax.scatter(
        data['sb'],
        fact * data['unique'],
        marker='*',
        s=20,
        color='C1',
        label='Unique',
        zorder=5
    )

    # total reduction on second axis
    ax2 = ax.twinx()

    reduction = 100 * (1.0 - data['unique'] / data['candidates'])

    ax2.scatter(
        data['sb'],
        reduction,
        marker='o',
        s=20,
        color='indianred',
        label='Total reduction',
        zorder=6
    )

    # median reduction
    med_red = np.median(reduction)
    ax2.axhline(
        y=med_red,
        color='indianred',
        lw=2,
        ls='dashed',
        label='median: {0:.1f}'.format(med_red),
        zorder=5
    )

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

    ax.scatter(
        data['mjd'],
        data['snr'] + 1,
        marker='x',
        color='black'
    )

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

    # 1) determine the good observations and their observing times
    with db_session:
        temp = select(
                (obs.id, obs.utc_start, obs.tobs)
                    for obs in schema.Observation
                )[:]

    print('Observations loaded: {0}'.format(len(temp)))

    # convert to pandas dataframe
    temp2 = {
        'id':               [item[0] for item in temp],
        'utc_start_str':    [item[1] for item in temp],
        'tobs':             [item[2] for item in temp],
    }

    df = DataFrame.from_dict(temp2)

    # convert to datetime
    df['utc_start'] = pd.to_datetime(df['utc_start_str'])

    df = df.sort_values(by='utc_start')

    observations = []

    for i in range(len(df) - 1):
        diff = df.at[i + 1, 'utc_start'] - df.at[i, 'utc_start']
        diff = diff.total_seconds()

        if 30 < diff < 900:
            if np.isfinite(df.at[i, 'tobs']):
                tobs = df.at[i, 'tobs']
            else:
                tobs = diff

            obs = {
                'id': df.at[i, 'id'],
                'tobs': tobs
            }

            observations.append(obs)

        else:
            continue

    print('Good observations: {0}'.format(len(observations)))

    # 2) create skymap
    config = get_config()
    nside = config['skymap']['nside']
    unit = config['skymap']['unit']

    m = Skymap(nside=nside, unit=unit)

    # 3) retrieve the beam information and fill in the exposure
    with db_session:
        for obs in observations:
            # ponyorm requires native python types in the generator expression
            obs_id = int(obs['id'])

            temp = select(
                    (beam.id, beam.number, beam.ra, beam.dec, beam.coherent,
                     obs.utc_start,
                     bc.cb_angle, bc.cb_x, bc.cb_y)
                        for obs in schema.Observation
                        for beam in obs.sps_candidate.beam
                        for bc in obs.beam_config
                        if obs.id == obs_id
                    )[:]

            # convert to pandas dataframe
            temp2 = {
                    'beam_id':      [item[0] for item in temp],
                    'number':       [item[1] for item in temp],
                    'ra':           [item[2] for item in temp],
                    'dec':          [item[3] for item in temp],
                    'coherent':     [item[4] for item in temp],
                    'utc_start':    [item[5] for item in temp],
                    'cb_angle':     [item[6] for item in temp],
                    'cb_x':         [item[7] for item in temp],
                    'cb_y':         [item[8] for item in temp]
                }

            df = DataFrame.from_dict(temp2)

            print('Observation, beams loaded: {0}, {1}'.format(obs_id, len(df)))

            coords = SkyCoord(
                ra=df['ra'],
                dec=df['dec'],
                unit=(units.hourangle, units.deg),
                frame='icrs'
            )

            # tobs in hours
            df['length'] = np.full(len(coords), obs['tobs'] / 3600.0)

            # tied-array beam coverage
            # 43 arcsec radius at l-band is typical
            df['radius'] = np.full(len(coords), 43.0 / 3600.0)

            # primary beam coverage
            mask_pb = (df['coherent'] == False) & (df['number'] == 0)
            # XXX: consider uhf vs. l-band
            df.loc[mask_pb, 'radius'] = 0.58

            # treat case of no detection in the incoherent beam
            if len(df[mask_pb]) == 0:
                print('No incoherent beam found.')
                mean_ra = np.mean(coords.ra.deg)
                mean_dec = np.mean(coords.dec.deg)

                mean_coord = SkyCoord(
                    ra=mean_ra,
                    dec=mean_dec,
                    unit=(units.deg, units.deg),
                    frame='icrs'
                )

                m.add_exposure(mean_coord, list(0.58), list(obs['tobs']))

            if len(df) == 1:
                print(df.to_string())

            m.add_exposure(coords, df['radius'], df['length'])

    m.save_to_file('skymap.pkl')
    print(m)

    # # galactic latitude thresholds
    # lat_thresh = [0, 5, 19.5, 42, 90]

    # # split into coherent and incoherent beams
    # mask_incoherent = (df['number'] == 0) & (df['coherent'] == False)
    # mask_coherent = np.logical_not(mask_incoherent)

    # coherent = data[mask_coherent].copy()
    # inco = data[mask_incoherent].copy()

    # coords_co = SkyCoord(
    #     ra=coherent['ra'],
    #     dec=coherent['dec'],
    #     unit=(units.hourangle, units.deg),
    #     frame='icrs'
    # )

    # coords_in = SkyCoord(
    #     ra=inco['ra'],
    #     dec=inco['dec'],
    #     unit=(units.hourangle, units.deg),
    #     frame='icrs'
    # )

    # # 1) coherent search
    # print('Coherent search')
    # print('---------------')

    # # XXX: assume constant tied-array beam area (deg2) for now
    # # this is about 1.6 arcmin2, or 0.44 mdeg2
    # a = 28.8 / 3600
    # b = 64.0 / 3600
    # area_co = np.pi * a * b

    # # XXX: assume 10 min tobs for the moment
    # tobs = 10 / 60.0

    # # output total stats
    # nbeams = len(coherent)
    # print('{0:16} {1:10.2f} deg2'.format('Total area', nbeams * area_co))
    # print('{0:16} {1:10.2f} hr deg2'.format('Total coverage', nbeams * area_co * tobs))

    # #plot_skymap_equatorial(coords_co, coherent, 'coherent', 8640)
    # #plot_skymap_galactic(coords_co, coherent, 'coherent', 300)

    # # do analysis by galactic latitude bins
    # for i in range(len(lat_thresh) - 1):
    #     start = lat_thresh[i]
    #     stop = lat_thresh[i + 1]
    #     print('Latitude bin: {0} <= abs(gb) < {1} deg'.format(start, stop))

    #     mask = np.logical_and(
    #         start <= np.abs(coords_co.galactic.b.deg),
    #         np.abs(coords_co.galactic.b.deg) < stop
    #     )

    #     nbeams = len(coherent[mask])

    #     print('{0:10} {1:10.2f} deg2'.format('Area', nbeams * area_co))
    #     print('{0:10} {1:10.2f} hr deg2'.format('Coverage', nbeams * area_co * tobs))
    #     print('')

    # # 2) incoherent search
    # print('')
    # print('Incoherent search')
    # print('-----------------')

    # # area of the primary beam (deg2) at 1284 MHz
    # area_inco = 0.97

    # # output total stats
    # nbeams = len(inco)
    # print('{0:16} {1:10.2f} deg2'.format('Total area', nbeams * area_inco))
    # print('{0:16} {1:10.2f} hr deg2'.format('Total coverage', nbeams * area_inco * tobs))

    # #plot_skymap_equatorial(coords_in, inco, 'inco', 190)
    # #plot_skymap_galactic(coords_in, inco, 'inco', 150)

    # # do analysis by galactic latitude bins
    # for i in range(len(lat_thresh) - 1):
    #     start = lat_thresh[i]
    #     stop = lat_thresh[i + 1]
    #     print('Latitude bin: {0} <= abs(gb) < {1} deg'.format(start, stop))

    #     mask = np.logical_and(
    #         start <= np.abs(coords_in.galactic.b.deg),
    #         np.abs(coords_in.galactic.b.deg) < stop
    #     )

    #     nbeams = len(inco[mask])

    #     print('{0:10} {1:10.2f} deg2'.format('Area', nbeams * area_inco))
    #     print('{0:10} {1:10.2f} hr deg2'.format('Coverage', nbeams * area_inco * tobs))
    #     print('')


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

    hb = ax.hexbin(
        coords.ra.hour,
        coords.dec.degree,
        C=data['tobs'],
        reduce_C_function=np.sum,
        gridsize=gridsize,
        bins='log',
        mincnt=1,
        linewidths=0.1,
        cmap='Reds'
    )

    # get unique area from the number of filled hexagons
    counts = hb.get_array()
    corners = hb.get_paths()

    # get the area of one hexagon
    xv = np.array([item[0][0] for item in corners[0].iter_segments()])
    yv = np.array([item[0][1] for item in corners[0].iter_segments()])
    area_hexagon = 15.0 * get_area_polygon(xv, yv)
    print('Area hexagon: {0:.5f} deg2'.format(area_hexagon))

    filled = counts[counts > 0]
    print('Number of hexagons: {0}'.format(len(counts)))
    print('Number of filled hexagons: {0}'.format(len(filled)))
    print('{0:16} {1:10.2f} deg2'.format('Unique area', len(filled) * area_hexagon))

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

    hb = ax.hexbin(
        -1 * gl_rad,
        gb_rad,
        C=data['tobs'],
        reduce_C_function=np.sum,
        gridsize=gridsize,
        bins='log',
        mincnt=1,
        linewidths=0.3,
        cmap='Reds'
    )

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


def run_timeonsky():
    """
    Run the processing for 'timeonsky' mode.
    """

    with db_session:
        temp = select(
                (obs.id, obs.utc_start, obs.tobs)
                    for obs in schema.Observation
                )[:]

    print('Observations loaded: {0}'.format(len(temp)))

    # convert to pandas dataframe
    temp2 = {
        'id':               [item[0] for item in temp],
        'utc_start_str':    [item[1] for item in temp],
        'tobs':             [item[2] for item in temp],
    }

    df = DataFrame.from_dict(temp2)

    # convert to datetime
    df['utc_start'] = pd.to_datetime(df['utc_start_str'])

    df = df.sort_values(by='utc_start')

    tobs = 0

    for i in range(len(df) - 1):
        diff = df.at[i + 1, 'utc_start'] - df.at[i, 'utc_start']
        diff = diff.total_seconds()

        if 30 < diff < 900:
            if np.isfinite(df.at[i, 'tobs']):
                tobs += df.at[i, 'tobs']
            else:
                tobs += diff

        else:
            continue

    print('Time on sky: {0:.1f} days'.format(tobs / (60 * 60 * 24.0)))


#
# MAIN
#

def main():
    args = parse_args()

    log = logging.getLogger('meertrapdb.make_plots')
    setup_logging()

    config = get_config()
    dbconf = config['db']

    db.bind(
        provider=dbconf['provider'],
        host=dbconf['host'],
        port=dbconf['port'],
        user=dbconf['user']['name'],
        passwd=dbconf['user']['password'],
        db=dbconf['database']
    )

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

    elif args.mode == 'timeonsky':
        run_timeonsky()

    log.info("All done.")


if __name__ == "__main__":
    main()
