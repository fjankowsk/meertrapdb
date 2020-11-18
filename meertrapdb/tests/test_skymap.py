# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path

from astropy.coordinates import SkyCoord
from astropy import units as u
import numpy as np
from numpy.testing import (assert_equal, assert_raises)

from meertrapdb.skymap import Skymap

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def test_creation():
    nside = 2**8
    unit = 'min'

    m = Skymap(nside=nside, unit=unit)
    print(m)


def test_addition_success():
    nside = 2**8
    unit = 'min'

    m1 = Skymap(nside=nside, unit=unit)
    print(m1)

    m2 = Skymap(nside=nside, unit=unit)
    print(m2)

    mtot = m1 + m2
    print(mtot)

    for param in ['arrangement', 'coordinate', 'dtype', 'nside', 'unit']:
        assert (getattr(mtot, param) == getattr(m1, param))
        assert (getattr(mtot, param) == getattr(m2, param))

    assert_equal(mtot.data, m1.data + m2.data)


def test_addition_fail():
    nside = 2**8
    unit = 'min'

    m1 = Skymap(nside=nside, unit=unit)
    print(m1)

    m2 = Skymap(nside=2**4, unit=unit)
    print(m2)

    with assert_raises(RuntimeError):
        m1 + m2

    m3 = Skymap(nside=nside, unit='bla')
    print(m3)

    with assert_raises(RuntimeError):
        m1 + m3

    m4 = Skymap(nside=2**4, unit='bla')
    print(m4)

    with assert_raises(RuntimeError):
        m1 + m4


def test_private_access():
    nside = 2**8
    unit = 'min'

    m = Skymap(nside=nside, unit=unit)

    with assert_raises(AttributeError):
        m.__data

    with assert_raises(AttributeError):
        m.data = None


def test_save():
    nside = 2**8
    unit = 'min'
    filename = 'skymap_test.npy'

    m = Skymap(nside=nside, unit=unit)
    print(m)

    m.save_to_file(filename)

    if not os.path.isfile(filename):
        raise RuntimeError('File does not exist.')


def test_size():
    nside = 2**10
    unit = 'min'

    m = Skymap(nside=nside, unit=unit)
    print(m.size)


def test_add_exposure():
    nside = 2**10
    unit = 'min'

    m = Skymap(nside=nside, unit=unit)

    coords = SkyCoord(
        ra=['04:37:15.8961737', '05:34:31.973', '08:35:20.61149', '16:44:49.273'],
        dec=['-47:15:09.110714', '+22:00:52.06', '-45:10:34.8751', '-45:59:09.71'],
        unit=(u.hour, u.deg),
        frame='icrs'
    )

    radius = np.full(len(coords), 0.58)
    length = np.full(len(coords), 10.0)

    m.add_exposure(coords, radius, length)
    print(m)

    m.show()


if __name__ == '__main__':
    import nose2
    nose2.main()
