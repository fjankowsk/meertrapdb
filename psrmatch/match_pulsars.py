# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Match pulsars.
#

from __future__ import print_function
import argparse
import logging
import os.path
import sys

import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.spatial import KDTree

from psrmatch.catalogue_helpers import parse_psrcat
from psrmatch.version import __version__

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def parse_args():
    # treat negative arguments
    for i, arg in enumerate(sys.argv):
        if (arg[0] == '-') and arg[1].isdigit(): sys.argv[i] = ' ' + arg

    parser = argparse.ArgumentParser(
        description="Find matching pulsars."
    )
    
    parser.add_argument(
        'ra',
        type=str,
        help='Right ascension in ICRS frame and in hh:mm:ss notation.'
    )

    parser.add_argument(
        'dec',
        type=str,
        help='Declination in ICRS frame and in hh:mm:ss notation.'
    )

    parser.add_argument(
        'dm',
        type=float,
        help='Dispersion measure.'
    )

    parser.add_argument(
        "--version",
        action="version",
        version=__version__
    )

    return parser.parse_args()

#
# MAIN
#

def main():
    args = parse_args()

    source = SkyCoord(ra=args.ra, dec=args.dec,
                     frame='icrs',
                     unit=(u.hourangle, u.deg))

    print('Source: {0}'.format(source.to_string('hmsdms')))
    print('DM: {0}'.format(args.dm))

    psrcat = parse_psrcat(
        os.path.join(
            os.path.dirname(__file__),
            'catalogues',
            'psrcat_v161.txt'
        )
    )

    # create search tree
    tree = KDTree(zip(psrcat['ra'], psrcat['dec']))

    # query
    result = tree.query(x=[source.ra.deg, source.dec.deg],
                        p=2,
                        k=5)

    dist, idx  = result

    print('Nearest neighbors:')
    for d, i in zip(dist, idx):
        info_str = '{0:.3f}: {1:10} {2:17} {3:17} {4:.3f}'.format(
            d,
            psrcat[i]['psrj'],
            psrcat[i]['ra_str'],
            psrcat[i]['dec_str'],
            psrcat[i]['dm']
        )

        print(info_str)

    # find matches
    dist_thresh = 1.5
    dm_thresh = 0.1

    match = None

    for d, i in zip(dist, idx):
        if d < dist_thresh \
        and abs(args.dm - psrcat[i]['dm']) / args.dm < dm_thresh:
            match = psrcat[i]
            print('Match found with distance: {0:.3f} deg'.format(d))
            break

    if match is None:
        print('No match found.')
    else:
        print('Found match: {0}, {1}, {2}, {3}'.format(
                match['psrj'],
                match['ra'],
                match['dec'],
                match['dm'])
            )



if __name__ == "__main__":
    main()
