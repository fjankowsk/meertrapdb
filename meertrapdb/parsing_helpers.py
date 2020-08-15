# -*- coding: utf-8 -*-
#
#   2019 - 2020 Fabian Jankowski
#   Parsing related helper functions.
#

import os.path

import numpy as np
from numpy.lib.recfunctions import append_fields


def parse_spccl_file(filename, version):
    """
    Parse a SPCCL file.

    Parameters
    ----------
    filename: str
        Name of the file to parse.

    Returns
    -------
    data: ~numpy.record
        The parsed data.
    version: int
        The spccl version to assume.

    Raises
    ------
    RuntimeError
        If the file does not exist.
    NotImplementedError
        If the requested SPCCL version is not implemented.
    """

    # check if file exists
    if not os.path.isfile(filename):
        raise RuntimeError("The SPCCL file does not exist: {0}".format(filename))

    if version == 1:
        names = [
            'index', 'mjd', 'dm', 'width', 'snr', 'beam',
            'ra', 'dec',
            'fil_file', 'plot_file'
        ]
    elif version == 2:
        names = [
            'index', 'mjd', 'dm', 'width', 'snr', 'beam', 'beam_mode',
            'ra', 'dec',
            'fil_file', 'plot_file'
        ]
    else:
        raise NotImplementedError('The requested SPCCL version is not implemented: {0}'.format(version))

    temp = np.genfromtxt(
        filename,
        dtype=None,
        names=names,
        delimiter="\t",
        encoding='ascii',
        autostrip=True
    )
    
    # treat case where the file is empty
    temp = np.atleast_1d(temp)

    # sanity check that the version is correct
    if version == 2:
        if np.unique(temp['beam_mode']) in ['C', 'I']:
            pass
        else:
            raise RuntimeError('Incorrect SPCCL version detected.')

    # add coherent flag
    coherent = np.zeros(len(temp), dtype=bool)

    data = append_fields(temp, 'coherent', coherent)

    if version == 1:
        data['coherent'] = True
    elif version >= 2:
        mask = (np.char.lower(temp['beam_mode']) == 'c')
        data['coherent'][mask] = True

    # ensure a unique running index
    data['index'] = range(len(data))

    return data


if __name__ == "__main__":
    cand_v1 = os.path.join(
        os.path.dirname(__file__),
        'tests',
        'candidates_v1.spccl.log'
    )

    cand_v2 = os.path.join(
        os.path.dirname(__file__),
        'tests',
        'candidates_v2.spccl.log'
    )

    for filename, version in zip([cand_v1, cand_v2], [1, 2]):
        print('Filename: {0}'.format(filename))
        print('Version: {0}'.format(version))
        data = parse_spccl_file(filename, version)

        for item in data:
            print(item)
