# coding: utf-8
#
#   Test the known source matcher.
#   2020 Fabian Jankowski
#

import time

from astropy.coordinates import SkyCoord
import astropy.units as units
import numpy as np

from psrmatch.matcher import Matcher

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


class MyTimer():
    def __init__(self):
        """
        A simple timing context manager for benchmarking purposes.
        """
        self.start = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.time()
        self.runtime = end - self.start

        msg = 'The function took: {0:.3f} s.'.format(self.runtime)
        print(msg)


def run_matcher(m, coords, dms):
    """
    Run the inner matching loop.
    """

    i = 0

    for source, dm in zip(coords, dms):
        match = m.find_matches(source, dm)

        if match is not None:
            i += 1

    return i


#
# MAIN
#

def main():
    # generate fake sources
    nsource = 20000

    # generate random parameters
    ras = np.random.uniform(0, 360, size=nsource)
    decs = np.random.uniform(-90, 25, size=nsource)
    dms = np.random.uniform(3, 1000, size=nsource)

    # parse coordinates
    coords = SkyCoord(
        ra=ras,
        dec=decs,
        unit=(units.degree, units.degree),
        frame='icrs'
    )

    print('Generated sources.')

    # prepare matcher
    m = Matcher()
    m.load_catalogue('psrcat')
    m.create_search_tree()

    print('Prepared matcher.')

    with MyTimer() as timer:
        imatch = run_matcher(m, coords, dms)

    print('Runtime: {0:.1f} s'.format(timer.runtime))
    print('Number of at least one matches: {0}'.format(imatch))
    print('Matching rate: {0:.1f} sources/s'.format(
        nsource / timer.runtime
        )
    )


if __name__ == "__main__":
    main()
