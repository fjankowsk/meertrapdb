# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path
import pickle

from astropy.coordinates import SkyCoord
import astropy.units as units
import numpy as np
from numpy.testing import assert_raises

from psrmatch.matcher import Matcher

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def test_catalogue_loading():
    m = Matcher()

    # simple loading
    m.load_catalogue('psrcat')

    np.testing.assert_equal(m.get_loaded_catalogues(), ['psrcat'])

    # double loading
    with assert_raises(RuntimeError):
        m.load_catalogue('psrcat')

    # unknown catalogue
    with assert_raises(NotImplementedError):
        m.load_catalogue('blablabla')


def test_catalogue_unloading():
    m = Matcher()

    np.testing.assert_equal(m.get_loaded_catalogues(), [])

    m.load_catalogue('psrcat')

    m.unload_catalogues()

    np.testing.assert_equal(m.get_loaded_catalogues(), [])


def test_matcher_readiness():
    m = Matcher()

    coords = SkyCoord(
        ra='08:35:20',
        dec='-45:10:34',
        unit=(units.degree, units.degree),
        frame='icrs'
    )

    dm = 67.97

    # not prepared
    with assert_raises(RuntimeError):
        m.find_matches(coords, dm)

    # working
    m.load_catalogue('psrcat')
    m.create_search_tree()

    m.find_matches(coords, dm)


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
                pickle.DEFAULT_PROTOCOL
            )


if __name__ == '__main__':
    import nose2
    nose2.main()
