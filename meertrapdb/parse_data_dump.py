# -*- coding: utf-8 -*-
#
#   2021 Fabian Jankowski
#   Process the sensor data dump.
#

import glob

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
    df['date'] = pd.to_datetime(df['value_ts'], unit='s')

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
    df['date'] = pd.to_datetime(df['value_ts'], unit='s')

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

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(
        df['date'],
        [1 for _ in range(len(df))]
    )

    ax.grid()
    ax.set_xlabel('MJD')

    fig.tight_layout()

    # add exposure to sky map
    config = get_config()
    smconfig = config['skymap']
    nside = smconfig['nside']
    unit = smconfig['unit']

    m = Skymap(nside=nside, unit=unit)

    coords = SkyCoord(
        ra=df['ra'],
        dec=df['dec'],
        unit=(units.deg, units.deg),
        frame='icrs'
    )

    pb_radius = smconfig['beam_radius']['l_band']['pb']

    for i in range(len(df) - 1):
        name = df.at[i, 'name']
        if name in ['', 'unset']:
            continue

        if np.isnan(coords[i].ra) or np.isnan(coords[i].dec):
            continue

        tobs = (df.at[i + 1, 'sample_ts'] - df.at[i, 'sample_ts']) / 3600.0
        #print(name, tobs, coords[i])
        #print(name, tobs)

        # remove short bogus pointings
        if tobs < 60.0 / 3600.0:
            continue

        m.add_exposure(
           [coords[i]],
           [pb_radius],
           [tobs]
        )

        # XXX: test
        #if i > 100:
        #    break

    # plot discoveries
    names = [
        'name',
        'ra',
        'dec',
        'type'
    ]

    df_sources = pd.read_csv(
        'sources.csv',
        sep=';',
        names=names,
        comment='#'
    )

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
