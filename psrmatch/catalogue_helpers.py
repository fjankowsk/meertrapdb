# -*- coding: utf-8 -*-
#
#   2019 Fabian Jankowski
#   Catalogue related helper functions.
#

from __future__ import print_function
import logging
import os.path

from astropy.coordinates import SkyCoord
import astropy.units as u
import numpy as np
from numpy.lib.recfunctions import append_fields

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def parse_psrcat(filename):
    """
    Parse psrcat output.
    """

    dtype = [
        ('number',int),
        ('psrj','|U32'), ('ref_psrj','|U32'),
        ('ra_str','|U64'), ('err_ra',float), ('ref_ra','|U32'),
        ('dec_str','|U64'), ('err_dec',float), ('ref_dec','|U32'),
        ('p0',float), ('err_p0',float), ('ref_p0','|U32'),
        ('dm',float), ('err_dm',float), ('ref_dm','|U32'),
    ]

    temp = np.genfromtxt(filename,
                         delimiter=';',
                         dtype=dtype,
                         encoding='ascii')
    
    coords = SkyCoord(ra=temp['ra_str'],
                      dec=temp['dec_str'],
                      frame='icrs', unit=(u.hourangle, u.deg))

    data = np.copy(temp)
    data = append_fields(data, 'ra', coords.ra.deg)
    data = append_fields(data, 'dec', coords.dec.deg)

    # remove non-radio pulsars
    data = data[np.isfinite(data['dm'])]

    return data
