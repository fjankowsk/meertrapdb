# -*- coding: utf-8 -*-
#
#   Perform multibeam sifting of the single-pulse candidates.
#

from __future__ import print_function
import argparse
import sys

from astropy import units
from astropy.coordinates import SkyCoord
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


def match_candidates(t_candidates, num_decimals, dm_thresh):
    """
    Match candidates based on MJD and DM.

    This function implements a simplistic multi-beam sifter.

    Parameters
    ----------
    t_candidates: ~np.record
        The meta data of the single-pulse candidates.
    num_decimals: int
        The number of decimals the detection MJDs are rounded to.
    dm_thresh: float
        The fractional DM tolerance to use for matching.

    Returns
    -------
    info: ~np.record
    """

    candidates = np.copy(t_candidates)

    candidates['mjd'] = np.around(candidates['mjd'], decimals=num_decimals)
    candidates = np.sort(candidates, order=['mjd', 'dm', 'snr'])

    cand_iter = np.nditer(candidates, flags=['f_index', 'refs_ok'], order='C')
    match_line = candidates[0]
    members = []

    dtype = [('index',int), ('is_head',bool), ('members',int), ('beams',int),
             ('max_separation',float)]
    info = np.zeros(len(candidates), dtype=dtype)

    while not cand_iter.finished:
        comp = candidates[cand_iter.index]

        info[cand_iter.index]['index'] = match_line['index']

        # check for matches in mjd and dm space
        if (comp['mjd'] == match_line['mjd']) and \
           (abs(comp['dm'] - match_line['dm']) / comp['dm'] < dm_thresh):
            members.append(comp)

            if (comp['snr'] > match_line['snr']):
                match_line = comp
        else:
            info[cand_iter.index]['is_head'] = True
            info[cand_iter.index]['members'] = len(members)
            info[cand_iter.index]['beams'] = len(set([item['beam'] for item in members]))

            # compute angular distance of the 'shower'
            # if len(matches) >= 2:
            #     ras = [item['ra'] for item in matches]
            #     decs = [item['dec'] for item in matches]
            #     max_separation = 0

            #     c = SkyCoord(ra=ras, dec=decs,
            #                  unit=(units.hourangle, units.deg),
            #                  frame='icrs')

            #     sep = c.separation(c)
            #     print(sep)

                # for i in range(len(matches)):
                #     c1 = SkyCoord(ra=matches[i]['ra'], dec=matches[i]['dec'],
                #                   unit=(units.hourangle, units.deg),
                #                   frame='icrs')

                #     for j in range(i, len(matches)):
                #         c2 = SkyCoord(ra=matches[j]['ra'], dec=matches[j]['dec'],
                #                   unit=(units.hourangle, units.deg),
                #                   frame='icrs')

                #         separation = c1.separation(c2).value

                #         if separation > max_separation:
                #             max_separation = separation

                #info[cand_iter.index]['max_separation'] = max_separation

            # step to next candidate
            match_line = comp
            members = []

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

    print('Total candidates: {0}'.format(len(candidates)))
    print('Unique candidates: {0}'.format(len(candidates[mask])))
    for field in ['matches', 'beams']:
        print('{0} (min, mean, median, max): {1}, {2}, {3}, {4}'.format(
            field.capitalize(),
            np.min(info[field]),
            np.mean(info[field]),
            np.median(info[field]),
            np.max(info[field]))
            )
    
    unique_cands = candidates[mask]
    num_matches = info['matches'][mask]

    with open('unique_cands.txt', 'w') as f:
        for i in range(len(unique_cands)):
            cand_str = '\t'.join(str(x) for x in unique_cands[i])
            info = "{0} {1}\n".format(cand_str, num_matches[i])
            f.write(info)


if __name__ == "__main__":
    main()
