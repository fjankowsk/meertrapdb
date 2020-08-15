# -*- coding: utf-8 -*-
#
#   2019 - 2020 Fabian Jankowski
#   Perform multi-beam clustering of single-pulse candidates.
#

import argparse
import logging
import sys

from astropy import units
from astropy.coordinates import SkyCoord
import numpy as np

from meertrapdb.clustering.clusterer import Clusterer
from meertrapdb.parsing_helpers import parse_spccl_file

# disable false positives of 'assigning to function call which does not return'
# pylint test case in numpy masks
# pylint: disable=E1111


def parse_args():
    """
    Parse the commandline arguments.

    Returns
    -------
    options: argparse.Parser object
    """

    parser = argparse.ArgumentParser(
        description='Perform multi-beam candidate clustering.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'filename',
        type=str
    )

    parser.add_argument(
        '--dm',
        type=float,
        default=0.02,
        help='Fractional DM tolerance.'
    )

    parser.add_argument(
        '--time',
        type=float,
        default=10.0,
        help='Time tolerance for matching in milliseconds.'
    )

    parser.add_argument(
        '--spccl_version',
        type=int,
        default=2,
        help='The version of the input SPCCL file.'
    )

    return parser.parse_args()


#
# MAIN
#

def main():
    args = parse_args()

    candidates = parse_spccl_file(args.filename, args.spccl_version)

    clust = Clusterer(args.time, args.dm)
    info = clust.match_candidates(candidates)

    mask = info['is_head']
    unique_cands = candidates[mask]
    num_matches = info['members'][mask]

    with open('unique_cands.txt', 'w') as f:
        for i in range(len(unique_cands)):
            cand_str = '\t'.join(str(x) for x in unique_cands[i])
            info = '{0} {1}\n'.format(cand_str, num_matches[i])
            f.write(info)
            print(info)


if __name__ == "__main__":
    main()
