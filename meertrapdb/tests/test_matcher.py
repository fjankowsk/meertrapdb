# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path
import pickle

from astropy.coordinates import SkyCoord
import astropy.units as units
import numpy as np

from psrmatch.matcher import Matcher

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def test_psrcat_matches():
    # known good output
    good_filename = os.path.join(
        os.path.dirname(__file__),
        'test_matcher_good_data.pkl'
    )

    if os.path.isfile(good_filename):
        with open(good_filename, 'rb') as fd:
            known_good = pickle.load(fd)

    else:
        # generate fake sources
        print('Generate fake sources.')

        nsource = 10000

        # generate random parameters
        ras = np.random.uniform(0, 360, size=nsource)
        decs = np.random.uniform(-90, 25, size=nsource)
        dms = np.random.uniform(3, 1000, size=nsource)

        known_good = {
            'ras': ras,
            'decs': decs,
            'dms': dms
        }

    # parse coordinates
    coords = SkyCoord(
        ra=known_good['ras'],
        dec=known_good['decs'],
        unit=(units.degree, units.degree),
        frame='icrs'
    )

    # prepare matcher
    m = Matcher()
    m.load_catalogue('psrcat')
    m.create_search_tree()

    matches = []

    for source, dm in zip(coords, known_good['dms']):
        match = m.find_matches(source, dm)
        matches.append(match)

    if os.path.isfile(good_filename):
        np.testing.assert_equal(matches, known_good['matches'])

    else:
        known_good = {
            'ras': ras,
            'decs': decs,
            'dms': dms,
            'matches': matches
        }

        with open(good_filename, 'wb') as fd:
            pickle.dump(
                known_good,
                fd,
                pickle.HIGHEST_PROTOCOL
            )


if __name__ == '__main__':
    import nose2
    nose2.main()
