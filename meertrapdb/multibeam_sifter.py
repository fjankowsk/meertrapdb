# -*- coding: utf-8 -*-
#
#   Perform multibeam sifting of the single-pulse candidates.
#

from __future__ import print_function
import argparse
import sys

import numpy as np

from meertrapdb.parsing_helpers import parse_spccl_file


def parse_args():
    """
    Parse the commandline arguments.

    Returns
    -------
    options: argparse.Parser object
    """

    parser = argparse.ArgumentParser(description='Multibeam candidate sifting code.')

    parser.add_argument('filename', type=str)

    parser.add_argument('--dm', type=float,
                        default=0.02,
                        help='Fractional DM tolerance. Default: 0.02')

    parser.add_argument('--mjd',
                        type=int,
                        default=7,
                        help='MJD is rounded off after this many decimals. Default: 7')

    return parser.parse_args()


def match_candidates(candidates, num_decimals, dm_thresh):
    """
    Match candidates based on MJD and DM.

    This function implements a simplistic multi-beam sifter.

    Parameters
    ----------
    num_decimals: int
        The number of decimals the detection MJDs are rounded to.
    dm_thresh: float
        The fractional DM tolerance to use for matching.

    Returns
    -------
    unique_cands: list (object)
    num_matches: list (int)
    """

    candidates['mjd'] = np.around(candidates['mjd'], decimals=num_decimals)
    candidates_sorted = np.sort(candidates, order=['mjd', 'dm', 'snr'])

    unique_cands = []
    cand_iter = np.nditer(candidates_sorted, flags=['f_index', 'refs_ok'], order='C')
    match_line = candidates_sorted[0]
    num_matches = []
    match_cnt = -1

    while not cand_iter.finished:
        # iterate first to match the first line
        if (candidates_sorted[cand_iter.index]['mjd'] == match_line['mjd']) and \
           ((candidates_sorted[cand_iter.index]['dm'] - match_line['dm']) / \
             candidates_sorted[cand_iter.index]['dm'] < dm_thresh):
            match_cnt += 1

            if (candidates_sorted[cand_iter.index]['snr'] > match_line['snr']):
                match_line = candidates_sorted[cand_iter.index]
        else:
            unique_cands.append(match_line)
            match_line = candidates_sorted[cand_iter.index]
            num_matches.append(match_cnt)
            match_cnt = 0

        cand_iter.iternext()

    return unique_cands, num_matches


#
# MAIN
#

def main():
    args = parse_args()

    candidates = parse_spccl_file(args.filename)

    unique_cands, num_matches = match_candidates(candidates, args.mjd, args.dm)

    with open('unique_cands.txt', 'w') as f:
        for i in range(len(unique_cands)):
            unique_cands[i] = '	'.join(str(x) for x in unique_cands[i])
            info = "{0} {1}\n".format(unique_cands[i], num_matches[i])
            f.write(info)


if __name__ == "__main__":
    main()
