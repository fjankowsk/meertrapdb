# -*- coding: utf-8 -*-
#
#   Perform multibeam sifting of the single-pulse candidates.
#

from __future__ import print_function
import argparse
import logging
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

    parser.add_argument('--dm',
                        type=float,
                        default=0.02,
                        help='Fractional DM tolerance. Default: 0.02')

    parser.add_argument('--time',
                        type=float,
                        default=10.0,
                        help='Time tolerance for matching in milliseconds. Default: 10.0')

    return parser.parse_args()


def match_candidates(t_candidates, time_thresh, dm_thresh):
    """
    Match candidates based on MJD and DM.

    This function implements a simplistic multi-beam sifter.

    Parameters
    ----------
    t_candidates: ~np.record
        The meta data of the single-pulse candidates.
    time_thresh: float
        The width of the matching box in ms.
    dm_thresh: float
        The fractional DM tolerance to use for matching.

    Returns
    -------
    info: ~np.record
    """

    candidates = np.copy(t_candidates)

    log = logging.getLogger('meertrapdb.multibeam_sifter')

    mjd_tol = 1E-3 * time_thresh / (24 * 60 * 60.0)
    log.info('Time tolerance: {0:.2f} ms'.format(time_thresh))
    log.info('MJD tolerance: {0:.10f}'.format(mjd_tol))
    log.info('DM tolerance: {0:.2f} %'.format(100 * dm_thresh))

    candidates = np.sort(candidates, order=['mjd', 'dm', 'snr'])

    dtype = [
        ('index',int), ('cluster_id',int),
        ('head',int), ('is_head',bool),
        ('members',int), ('beams',int),
        ('processed',bool)
        ]
    info = np.zeros(len(candidates), dtype=dtype)

    # fill in the candidate indices
    info['index'] = candidates['index']

    cluster_id = 0

    for i in range(len(candidates)):
        cand = candidates[i]

        # check if the candidate was already processed
        mask_cand = (info['index'] == cand['index'])
        if info['processed'][mask_cand]:
            log.info('Candidate was already processed, skipping it: {0}'.format(cand['index']))
            continue

        mask_in_box = np.logical_and(
            np.abs(candidates['mjd'] - cand['mjd']) <= mjd_tol,
            np.abs(candidates['dm'] - cand['dm']) / cand['dm'] <= dm_thresh
        )

        mask_not_processed = np.logical_not(info['processed'])

        mask = np.logical_and(mask_in_box, mask_not_processed)

        members = candidates[mask]

        # skip further in the candidates
        if len(members) == 0:
            log.info('No members found.')
            continue

        members = np.sort(members, order='snr')

        # the cluster head is the one with the highest snr
        head = members[-1]

        # fill in all members
        info['head'][mask] = head['index']
        info['cluster_id'][mask] = cluster_id
        info['members'][mask] = len(members)
        info['beams'][mask] = len(np.unique(members['beam']))
        info['processed'][mask] = True

        # specially mark head
        mask_head = (info['index'] == head['index'])
        info['is_head'][mask_head] = True

        cluster_id += 1

    # sanity checks
    # 1) candidate indices must be unique
    if not len(info['index']) == len(np.unique(info['index'])):
        raise RuntimeError('The candidate indices are not not unique.')

    # 2) the number of cluster heads must match
    if not len(info[info['is_head']]) == len(np.unique(info['head'])):
        raise RuntimeError('The number of cluster heads is incorrect.')

    # 3) check that all candidates have been processed
    if not np.all(info['processed']):
        raise RuntimeError('Not all candidates have been processed.')

    # output sifting statistics
    mask = info['is_head']

    log.info('Total candidates: {0}'.format(len(candidates)))
    if len(candidates) > 0:
        log.info('Cluster heads: {0} ({1:.2f})'.format(
            len(candidates[mask]),
            100 * len(candidates[mask]) / float(len(candidates))
            ))

        for field in ['members', 'beams']:
            log.info('{0} (min, mean, median, max): {1}, {2}, {3}, {4}'.format(
                field.capitalize(),
                np.min(info[field]),
                np.mean(info[field]),
                np.median(info[field]),
                np.max(info[field]))
                )

    # display some debug output
    for item, cand in zip(info, candidates):
        log.debug('{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}'.format(
            item['index'], item['cluster_id'], item['is_head'],
            item['members'], item['beams'], item['head'],
            cand['mjd'], cand['dm'], cand['snr']
            ))

    info = np.sort(info, order='index')

    return info


#
# MAIN
#

def main():
    args = parse_args()

    candidates = parse_spccl_file(args.filename)

    info = match_candidates(candidates, args.time, args.dm)

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
