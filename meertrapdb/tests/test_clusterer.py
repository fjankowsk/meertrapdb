# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path

from meertrapdb.parsing_helpers import parse_spccl_file
from meertrapdb.multibeam_sifter import match_candidates


def test_multibeam_clusterer():
    # XXX: we need a file with duplicates
    spccl_file = os.path.join(
        os.path.dirname(__file__),
        'candidates_v2.spccl.log'
    )

    candidates = parse_spccl_file(spccl_file, 2)
    print('Number of candidates: {0}'.format(len(candidates)))

    info = match_candidates(candidates, 10.0, 0.02)

    mask = info['is_head']
    heads = candidates[mask]
    num_matches = info['beams'][mask]

    print('Cluster heads: {0}'.format(len(heads)))

    for head, nmatch in zip(heads, num_matches):
        print('{0} {1}'.format(head, nmatch))


if __name__ == '__main__':
    import nose2
    nose2.main()
