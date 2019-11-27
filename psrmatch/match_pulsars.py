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


class Matcher(object):
    """
    Match sources to catalogues of known sources.
    """

    def __init__(self, dist_thresh=1.5, dm_thresh=10.0):
        """
        Match sources to catalogues of known sources.

        Parameters
        ----------
        dist_thresh: float
            Distance threshold in degree.
        dm_thresh: float
            DM threshold in per cent.
        """

        self.dist_thresh = dist_thresh
        self.dm_thresh = dm_thresh / 100.0
        self.catalogue = None
        self.tree = None
        self.log = logging.getLogger('meertrapdb.matcher')


    def load_catalogue(self, catalogue):
        """
        Load a known-source catalogue.

        Parameters
        ----------
        catalogue: ~np.record
            The catalogue data.
        """

        self.catalogue = catalogue


    def create_search_tree(self):
        """
        Create a k-d search tree from the catalogue.
        """

        self.tree = KDTree(
            zip(self.catalogue['ra'], self.catalogue['dec'])
            )


    def query_search_tree(self, source):
        """
        Query the search tree.

        Parameters
        ----------
        source: ~astropy.coordinates.SkyCoord
            The source to check.

        Returns
        -------
        result: [~np.array, ~np.array]
            The distances and indices of the nearest neighbors.
        """

        result = self.tree.query(
            x=[source.ra.deg, source.dec.deg],
            p=2,
            k=5)

        dist, idx  = result

        print('Nearest neighbors:')
        for d, i in zip(dist, idx):
            info_str = '{0:.3f}: {1:10} {2:17} {3:17} {4:.3f}'.format(
                d,
                self.catalogue[i]['psrj'],
                self.catalogue[i]['ra_str'],
                self.catalogue[i]['dec_str'],
                self.catalogue[i]['dm']
            )

            print(info_str)

        return result


    def find_matches(self, source, dm):
        """
        Find matches in spatial - DM space.

        Parameters
        ----------
        source: ~astropy.coordinates.SkyCoord
            The source to check.
        dm: float
            The dispersion measure of the source.
        """

        dist, idx  = self.query_search_tree(source)

        self.log.info('Using distance threshold: {0} deg'.format(self.dist_thresh))
        self.log.info('Using DM threshold: {0}'.format(self.dm_thresh))

        match = None

        for d, i in zip(dist, idx):
            if d < self.dist_thresh \
            and abs(dm - self.catalogue[i]['dm']) / dm < self.dm_thresh:
                match = self.catalogue[i]
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

        return match


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

    m = Matcher()

    m.load_catalogue(psrcat)

    m.create_search_tree()

    m.find_matches(source, args.dm)


if __name__ == "__main__":
    main()
