# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path

import numpy as np
from numpy.testing import assert_raises

from meertrapdb.clustering.clusterer import Clusterer
from meertrapdb.parsing_helpers import parse_spccl_file


def test_multibeam_clustering():
    # known good output
    good_filename = os.path.join(
        os.path.dirname(__file__),
        'test_clusterer_good_info.npy'
    )
    good_info = np.load(good_filename)

    spccl_file = os.path.join(
        os.path.dirname(__file__),
        'test_clusterer_candidates.spccl.log'
    )

    candidates = parse_spccl_file(spccl_file, 1)
    print('Number of candidates: {0}'.format(len(candidates)))

    clust = Clusterer(10.0, 0.02)
    info = clust.match_candidates(candidates)

    mask = info['is_head']
    heads = candidates[mask]

    print('Cluster heads: {0}'.format(len(heads)))

    np.testing.assert_equal(good_info, info)


def test_private_access():
    clust = Clusterer(10.0, 0.02)

    with assert_raises(AttributeError):
        clust.__time_thresh

    with assert_raises(AttributeError):
        clust.__dm_thresh


def test_parameter_access():
    clust = Clusterer(10.0, 0.02)

    assert (clust.time_thresh == 10.0)
    assert (clust.dm_thresh == 0.02)


def test_parameter_change():
    clust = Clusterer(10.0, 0.02)

    clust.time_thresh = 20.0
    clust.dm_thresh = 0.05

    assert (clust.time_thresh == 20.0)
    assert (clust.dm_thresh == 0.05)


def test_invalid_parameters():
    clust = Clusterer(10.0, 0.02)

    with assert_raises(RuntimeError):
        clust.time_thresh = -20.0

    with assert_raises(RuntimeError):
        clust.dm_thresh = 'bla'

    assert (clust.time_thresh == 10.0)
    assert (clust.dm_thresh == 0.02)


if __name__ == '__main__':
    import nose2
    nose2.main()
