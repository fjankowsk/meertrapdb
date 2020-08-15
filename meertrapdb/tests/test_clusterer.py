# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path

import numpy as np

from meertrapdb.parsing_helpers import parse_spccl_file
from meertrapdb.multibeam_sifter import match_candidates


def test_multibeam_clusterer():
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

    info = match_candidates(candidates, 10.0, 0.02)

    mask = info['is_head']
    heads = candidates[mask]

    print('Cluster heads: {0}'.format(len(heads)))

    np.testing.assert_equal(good_info, info)


if __name__ == '__main__':
    import nose2
    nose2.main()
