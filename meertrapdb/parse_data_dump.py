# -*- coding: utf-8 -*-
#
#   2021 Fabian Jankowski
#   Process the sensor data dump.
#

import glob
import os.path

from astropy import units
from astropy.coordinates import SkyCoord
import katpoint
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from meertrapdb.config_helpers import get_config
from meertrapdb.skymap import Skymap

# astropy.units generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def run_timeline():
    """
    Run the processing for timeline mode.
    """

    files = glob.glob('fbfuse*.csv')
    files = sorted(files)

    frames = []

    for item in files:
        names = [
            'name',
            'sample_ts',
            'value_ts',
            'value',
            'status'
        ]

        temp = pd.read_csv(
            item,
            names=names,
            na_values='0',
            quotechar='"'
        )

        frames.append(temp)

    df = pd.concat(
        frames,
        ignore_index=True,
        sort=False
    )

    # convert to dates
    df['date'] = pd.to_datetime(df['sample_ts'], unit='s')

    # add unit field
    df['unit'] = ''

    # convert to mhz
    mask = np.logical_or(
        df['name'] == 'fbfuse_1_fbfmc_array_1_bandwidth',
        df['name'] == 'fbfuse_1_fbfmc_array_1_centre_frequency'
    )
    df.loc[mask, 'value'] = df.loc[mask, 'value'] * 1E-6
    df.loc[mask, 'unit'] = 'MHz'

    # add unit
    mask = (df['name'] == 'fbfuse_1_fbfmc_array_1_coherent_beam_count')
    df.loc[mask, 'unit'] = '#'

    print(df.info())
    print(np.unique(df['name']))

    fig, axs = plt.subplots(
        nrows=len(np.unique(df['name'])),
        ncols=1,
        sharex=True,
        sharey=False
    )

    for i, item in enumerate(np.unique(df['name'])):
        print('Plotting: {0}'.format(item))

        mask = (df['name'] == item)
        sel = df.loc[mask]

        axs[i].scatter(
            sel['date'],
            sel['value'],
            color='C0',
            marker='.',
            s=4,
            label=item,
            zorder=3
        )

        axs[i].grid()
        axs[i].set_ylabel('({0})'.format(sel.at[0, 'unit']))
        axs[i].legend(loc='best', frameon=False)

    axs[-1].set_xlabel('UTC')

    fig.tight_layout()

    fig.savefig(
        'timeline.png',
        dpi=300
    )


def get_cfreq_data():
    """
    Get the centre frequency information.

    Returns
    -------
    df: ~pandas.DataFrame
        The centre frequency data.
    """

    files = glob.glob('fbfuse_sensor_dump/*_centre_frequency_*.csv')
    files = sorted(files)

    if not len(files) > 0:
        raise RuntimeError('Need to provide input files.')

    frames = []

    for item in files:
        names = [
            'name',
            'sample_ts',
            'value_ts',
            'status',
            'value'
        ]

        temp = pd.read_csv(
            item,
            names=names,
            quotechar='"'
        )

        frames.append(temp)

    df = pd.concat(
        frames,
        ignore_index=True,
        sort=False
    )

    # sort
    df = df.sort_values(by='sample_ts')
    df = df.reindex()

    # convert to dates
    df['date'] = pd.to_datetime(df['sample_ts'], unit='s')

    return df


def run_pointing():
    """
    Run the processing for pointing mode.
    """

    files = glob.glob('fbfuse_sensor_dump/*_phase_reference_*.csv')
    files = sorted(files)

    if not len(files) > 0:
        raise RuntimeError('Need to provide input files.')

    frames = []

    for item in files:
        names = [
            'name',
            'sample_ts',
            'value_ts',
            'status',
            'value'
        ]

        temp = pd.read_csv(
            item,
            names=names,
            quotechar='"'
        )

        frames.append(temp)

    df = pd.concat(
        frames,
        ignore_index=True,
        sort=False
    )

    # sort
    df = df.sort_values(by='sample_ts')
    df = df.reindex()

    # convert to dates
    df['date'] = pd.to_datetime(df['sample_ts'], unit='s')

    # parse targets
    df['value'] = df['value'].str.strip('"')

    coords = []

    for i in range(len(df)):
        raw = df.at[i, 'value']

        name = ''
        ra = np.nan
        dec = np.nan

        try:
            target = katpoint.Target(raw)
            name = target.name
            result = target.astrometric_radec()
            ra = np.degrees(result[0])
            dec = np.degrees(result[1])
        except Exception:
            pass

        coords.append([name, ra, dec])

    df['name'] = [item[0] for item in coords]
    df['ra'] = [item[1] for item in coords]
    df['dec'] = [item[2] for item in coords]

    # add observing time
    df['tobs'] = df['sample_ts'].diff()

    mask = (df['name'] == '') | \
           (df['name'] == 'unset') | \
           (df['ra'] == 0) | \
           (df['dec'] == 0) | \
           df['ra'].isnull() | \
           df['dec'].isnull()

    df.loc[mask, 'tobs'] = np.nan

    # remove short bogus pointings
    mask = (df['tobs'] < 60.0)
    df.loc[mask, 'tobs'] = np.nan

    # remove pointings at the end of a session
    mask = (df['tobs'] > 3600.0)
    df.loc[mask, 'tobs'] = np.nan

    # truncate (incorrect) long pointings
    mask = (df['tobs'] > 700.0)
    df.loc[mask, 'tobs'] = 600.0

    print(df.to_string(columns=['name', 'tobs']))

    # plot tobs
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(
        df['date'],
        df['tobs'],
        marker='.',
        color='black',
        s=0.5,
        zorder=3
    )

    ax.grid()
    ax.set_xlabel('MJD')
    ax.set_ylabel('tobs (s)')

    fig.tight_layout()

    fig.savefig(
        'tobs_timeline.png',
        dpi=300
    )

    # histogram of tobs
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.hist(
        df['tobs'],
        histtype='step',
        bins=30,
        color='black',
        lw=1.5,
        zorder=3
    )

    ax.grid()
    ax.set_xlabel('tobs (s)')
    ax.set_ylabel('Number')

    fig.tight_layout()

    fig.savefig(
        'tobs_hist.png',
        dpi=300
    )

    # figure out observing band
    df_cfreq = get_cfreq_data()

    bands = []

    for i in range(len(df)):
        band = ''

        if np.isnan(df.at[i, 'tobs']):
            pass
        else:
            start = df.at[i, 'date']
            end = df.at[i, 'date'] + pd.to_timedelta(df.at[i, 'tobs'], unit='s')
            #print('Start, end: {0}, {1}'.format(start, end))

            mask = (df_cfreq['date'] >= start) & (df_cfreq['date'] <= end)
            sel = df_cfreq.loc[mask]

            #print(len(sel))

            if len(sel) > 0:
                # use value in first row
                # XXX: use a better method
                cfreq = sel['value'].iat[0]

                if cfreq < 1.0E9:
                    band = 'u'
                elif 1.0E9 < cfreq < 2.0E9:
                    band = 'l'
                elif cfreq > 2.0E9:
                    band = 's'
                else:
                    raise RuntimeError('Band unknown: {0}'.format(cfreq))

        bands.append(band)

    df['band'] = bands

    # add exposure to sky map
    config = get_config()
    smconfig = config['skymap']
    nside = smconfig['nside']
    unit = smconfig['unit']

    m = Skymap(nside=nside, unit=unit)

    mask = np.logical_not(df['tobs'].isnull())
    sel = df[mask].copy()

    print('Total time span: {0:.1f} days'.format(
        (sel['date'].max() - sel['date'].min()).total_seconds() / 86400.0
        )
    )

    print('Total tobs: {0:.1f} days'.format(sel['tobs'].sum() / 86400.0))

    print('Average observing time: {0:.2f} hours / day'.format(
        24 * sel['tobs'].sum() / (sel['date'].max() - sel['date'].min()).total_seconds()
        )
    )

    coords = SkyCoord(
        ra=sel['ra'],
        dec=sel['dec'],
        unit=(units.deg, units.deg),
        frame='icrs'
    )

    # add primary beam radii
    pb_radius_l = smconfig['beam_radius']['l_band']['pb']
    pb_radius_u = smconfig['beam_radius']['uhf_band']['pb']

    # use l-band as default
    sel['radius'] = pb_radius_l

    mask = (sel['band'] == 'l')
    sel.loc[mask, 'radius'] = pb_radius_l

    mask = (sel['band'] == 'u')
    sel.loc[mask, 'radius'] = pb_radius_u

    m.add_exposure(
        coords,
        sel['radius'],
        sel['tobs'] / 3600.0
    )

    # plot discoveries
    names = [
        'name',
        'ra',
        'dec',
        'type'
    ]

    if os.path.isfile('sources.csv'):
        df_sources = pd.read_csv(
            'sources.csv',
            sep=';',
            names=names,
            comment='#'
        )
    else:
        df_sources = None

    #m.save_to_file('skymap_from_data_dump.pkl')
    print(m)

    m.show(
        coordinates='galactic',
        sources=df_sources
    )

    m.show(
        coordinates='equatorial',
        sources=df_sources
    )


#
# MAIN
#

def main():
    run_pointing()

    plt.show()

    print('All done.')


if __name__ == "__main__":
    main()
