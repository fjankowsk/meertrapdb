# -*- coding: utf-8 -*-
#
#   Perform multibeam sifting of the single-pulse candidates.
#

from __future__ import print_function
import argparse
import sys

import numpy as np


def parse_args():
    """
    Parse the commandline arguments.

    Returns
    -------
    options: argparse.Parser object
    """

    parser = argparse.ArgumentParser(description='Multibeam candidate sifting code.')

    parser.add_argument('file', type=str)

    parser.add_argument('-dm', type=float,
                        nargs=1,
                        default=[0.02],
                        help='Fractional DM tolerance. Default: 0.02')

    parser.add_argument('-mjd',
                        type=int,
                        nargs=1,
                        default=[7],
                        help='MJD is rounded off after this many decimals. Default: 7')

    return parser.parse_args()


def parse_spccl_file(filename):
    """
    Parse an SPCCL candidate file.

    Returns
    -------
    data: ~np.record
    """

    dtype = [('a',int), ('b',float), ('c',float), ('d',float), ('e',float), ('f',int),
              ('g','|S12'), ('h','|S12'), ('i','|S23'), ('j','|S128')]
    names = ["N", "MJD", "DM", "WIDTH", "SNR", "BEAM", "RAJ", "DECJ", "FILFILE", "JPEG"]

    data = np.genfromtxt(filename, names=names, dtype=dtype)

    return data


#
# MAIN
#

def main():
    args = parse_args()

    candidates = parse_spccl_file(args.filename)

    candidates['MJD'] = np.around(candidates['MJD'], decimals=args.mjd)
    candidates_sorted = np.sort(candidates, order=['MJD', 'DM', 'SNR'])
    unique_cands = []
    cand_iter = np.nditer(candidates_sorted, flags=['f_index', 'refs_ok'], order='C')
    match_line = candidates_sorted[0]
    num_matches = []
    match_cnt = -1

    while not cand_iter.finished:
        # iterate first to match the first line
        if (candidates_sorted[cand_iter.index][1] == match_line[1]) and \
           ((candidates_sorted[cand_iter.index][2] - match_line[2]) / \
             candidates_sorted[cand_iter.index][2] < args.dm):
            match_cnt += 1

            if (candidates_sorted[cand_iter.index][4] > match_line[4]):
                match_line = candidates_sorted[cand_iter.index]
        else:
            unique_cands.append(match_line)
            match_line = candidates_sorted[cand_iter.index]
            num_matches.append(match_cnt)
            match_cnt = 0

        cand_iter.iternext()

    with open ("unique_cands.txt", "w") as f:
        for i in range(len(unique_cands)):
            unique_cands[i] = '	'.join(str(x) for x in unique_cands[i])
            f.write(unique_cands[i] + "	" + str(num_matches[i])+"\n")


if __name__ == "__main__":
    main()
