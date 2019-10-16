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
    info: ~np.record
    """

    candidates['mjd'] = np.around(candidates['mjd'], decimals=num_decimals)
    candidates_sorted = np.sort(candidates, order=['mjd', 'dm', 'snr'])

    cand_iter = np.nditer(candidates_sorted, flags=['f_index', 'refs_ok'], order='C')
    match_line = candidates_sorted[0]
    match_cnt = -1

    dtype = [('index',int), ('uniq',bool), ('matches',int)]
    info = np.zeros(len(candidates), dtype=dtype)

    while not cand_iter.finished:
        info[cand_iter.index]['index'] = match_line['index']

        # iterate first to match the first line
        if (candidates_sorted[cand_iter.index]['mjd'] == match_line['mjd']) and \
           ((candidates_sorted[cand_iter.index]['dm'] - match_line['dm']) / \
             candidates_sorted[cand_iter.index]['dm'] < dm_thresh):
            match_cnt += 1

            if (candidates_sorted[cand_iter.index]['snr'] > match_line['snr']):
                match_line = candidates_sorted[cand_iter.index]
        else:
            info[cand_iter.index]['uniq'] = True
            info[cand_iter.index]['matches'] = match_cnt

            # step to next candidate
            match_line = candidates_sorted[cand_iter.index]
            match_cnt = 0

        cand_iter.iternext()
    
    info = np.sort(info, order='index')

    return info


#
# MAIN
#

def main():
    args = parse_args()

    candidates = parse_spccl_file(args.filename)

    info = match_candidates(candidates, args.mjd, args.dm)

    mask = info['uniq']
    unique_cands = candidates[mask]
    num_matches = info['matches'][mask]

    with open('unique_cands.txt', 'w') as f:
        for i in range(len(unique_cands)):
            cand_str = '\t'.join(str(x) for x in unique_cands[i])
            info = "{0} {1}\n".format(cand_str, num_matches[i])
            f.write(info)


if __name__ == "__main__":
    main()
