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

from psrmatch.catalogue_helpers import parse_psrcat
from psrmatch.matcher import Matcher
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


def setup_logging(level=logging.INFO):
    """
    Setup the logging configuration.
    """

    log = logging.getLogger('psrmatch')

    log.setLevel(logging.DEBUG)
    log.propagate = False

    # log to console
    console = logging.StreamHandler()
    console.setLevel(level)
    fmt = "%(asctime)s, %(processName)s, %(name)s, %(module)s, %(levelname)s: %(message)s"
    console_formatter = logging.Formatter(fmt)
    console.setFormatter(console_formatter)
    log.addHandler(console)


#
# MAIN
#

def main():
    args = parse_args()
    setup_logging()

    source = SkyCoord(
        ra=args.ra,
        dec=args.dec,
        frame='icrs',
        unit=(u.hourangle, u.deg)
    )

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
