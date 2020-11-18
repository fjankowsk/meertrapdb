# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#   Cluster single-pulse candidates in various ways.
#

import logging

import numpy as np

# disable false positives of 'assigning to function call which does not return'
# pylint test case in numpy masks
# pylint: disable=E1111


class Clusterer(object):
    """
    Cluster single-pulse candidates in various ways.
    """

    name = 'Clusterer'

    def __init__(self, time_thresh=10.0, dm_thresh=0.02):
        """
        Cluster single-pulse candidates in various ways.

        Parameters
        ----------
        time_thresh: float (default: 10.0)
            The width of the matching box in ms.
        dm_thresh: float (default: 0.02)
            The fractional DM tolerance to use for matching.
        """

        self.__time_thresh = None
        self.__dm_thresh = None
        self.__log = logging.getLogger('meertrapdb.clustering.clusterer')

        # use validation in the setter functions
        self.time_thresh = time_thresh
        self.dm_thresh = dm_thresh

    def __repr__(self):
        """
        Representation of the object.
        """

        info_dict = {
            'time_thresh': self.time_thresh,
            'dm_thresh': self.dm_thresh
        }

        info_str = '{0}'.format(info_dict)

        return info_str

    def __str__(self):
        """
        String representation of the object.
        """

        info_str = '{0}: {1}'.format(self.name, repr(self))

        return info_str

    @property
    def time_thresh(self):
        """
        The width of the matching box in ms.
        """

        return self.__time_thresh

    @time_thresh.setter
    def time_thresh(self, time):
        """
        Set the width of the matching box in ms.

        Raises
        ------
        RuntimeError
            If time threshold is invalid.
        """

        if type(time) == float \
        and time > 0:
            self.__time_thresh = time
        else:
            raise RuntimeError('Time threshold is invalid: {0}'.format(time))

    @property
    def dm_thresh(self):
        """
        The fractional DM tolerance to use for matching.
        """

        return self.__dm_thresh

    @dm_thresh.setter
    def dm_thresh(self, thresh):
        """
        Set the fractional DM tolerance to use for matching.

        Raises
        ------
        RuntimeError
            If DM threshold is invalid.
        """

        if type(thresh) == float \
        and thresh > 0:
            self.__dm_thresh = thresh
        else:
            raise RuntimeError('DM threshold is invalid: {0}'.format(thresh))

    def match_candidates(self, t_candidates):
        """
        Match candidates based on MJD and DM.

        This function implements a simplistic multi-beam sifter.

        Parameters
        ----------
        t_candidates: ~np.record
            The meta data of the single-pulse candidates.

        Returns
        -------
        info: ~np.record
            Information about the matching.

        Raises
        ------
        RuntimeError
            On errors.
        """

        candidates = np.copy(t_candidates)

        mjd_tol = 1E-3 * self.time_thresh / (24 * 60 * 60.0)
        self.__log.info('Time tolerance: {0:.2f} ms'.format(self.time_thresh))
        self.__log.info('MJD tolerance: {0:.10f}'.format(mjd_tol))
        self.__log.info('DM tolerance: {0:.2f} %'.format(100 * self.dm_thresh))

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
                self.__log.debug('Candidate was already assigned a cluster, skipping it: {0}'.format(cand['index']))
                continue

            mask_in_box = np.logical_and(
                np.abs(candidates['mjd'] - cand['mjd']) <= mjd_tol,
                np.abs(candidates['dm'] - cand['dm']) / cand['dm'] <= self.dm_thresh
            )

            mask_not_processed = np.logical_not(info['processed'])

            mask = np.logical_and(mask_in_box, mask_not_processed)

            members = candidates[mask]

            # skip further in the candidates
            if len(members) == 0:
                self.__log.info('No members found.')
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

        self.__log.info('Total candidates: {0}'.format(len(candidates)))
        if len(candidates) > 0:
            self.__log.info('Cluster heads: {0} ({1:.2f})'.format(
                len(candidates[mask]),
                100 * len(candidates[mask]) / float(len(candidates))
                )
            )

            self.__log.info('Clusters: {0}'.format(np.max(info['cluster_id']) + 1))

            for field in ['members', 'beams']:
                self.__log.info('{0} (min, mean, median, max): {1}, {2}, {3}, {4}'.format(
                    field.capitalize(),
                    np.min(info[field]),
                    np.mean(info[field]),
                    np.median(info[field]),
                    np.max(info[field])
                    )
                )

        # display some debug output
        for item, cand in zip(info, candidates):
            self.__log.debug('{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}'.format(
                item['index'],
                item['cluster_id'],
                item['is_head'],
                item['members'],
                item['beams'],
                item['head'],
                cand['mjd'],
                cand['dm'],
                cand['snr']
                )
            )

        info = np.sort(info, order='index')

        return info
