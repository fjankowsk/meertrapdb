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

    Parameters
    ----------
    filename: str
        The filename of the pulsar catalogue output.

    Returns
    -------
    data: ~np.record
        The catalogue data as a numpy record.

    Raises
    ------
    RuntimeError
        If the catalogue data could not be parsed.
    """

    if not os.path.isfile(filename):
        raise RuntimeError('The file does not exist: {0}'.format(filename))

    dtype = [
        ('number',int),
        ('psrj','|U32'), ('ref_psrj','|U32'),
        ('ra_str','|U64'), ('err_ra',float), ('ref_ra','|U32'),
        ('dec_str','|U64'), ('err_dec',float), ('ref_dec','|U32'),
        ('p0',float), ('err_p0',float), ('ref_p0','|U32'),
        ('dm',float), ('err_dm',float), ('ref_dm','|U32'),
        ('type','|U32'), ('ref_type','|U32')
    ]

    temp = np.genfromtxt(filename,
                         delimiter=';',
                         dtype=dtype,
                         encoding='ascii')

    coords = SkyCoord(ra=temp['ra_str'],
                      dec=temp['dec_str'],
                      frame='icrs', unit=(u.hourangle, u.deg))

    # add equatorial degree fields
    data = np.copy(temp)
    data = append_fields(data, 'ra', coords.ra.deg)
    data = append_fields(data, 'dec', coords.dec.deg)

    # add catalogue field
    catalogue = np.array(len(data), dtype='|U32')
    catalogue[:] = u'psrcat'
    data = append_fields(data, 'catalogue', catalogue)

    # fill default type
    data['type'][data['type'] == '*'] = 'pulsar'

    # remove non-radio pulsars
    data = data[np.isfinite(data['dm'])]

    # sanity check
    if len(data) == 0:
        raise RuntimeError('No catalogue data loaded.')

    return data
