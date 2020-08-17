# coding: utf-8
#
#   Benchmark the multi-beam clusterer.
#   2020 Fabian Jankowski
#

import os.path
import time

import numpy as np

from meertrapdb.clustering.clusterer import Clusterer
from meertrapdb.parsing_helpers import parse_spccl_file


class MyTimer():
    def __init__(self):
        """
        A simple timing context manager for benchmarking purposes.
        """
        self.start = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = time.time()
        self.runtime = end - self.start

        msg = 'The function took: {0:.3f} s.'.format(self.runtime)
        print(msg)


#
# MAIN
#

def main():
    test_file = os.path.join(
        os.path.dirname(__file__),
        '..',
        'tests',
        'test_clusterer_candidates.spccl.log'
    )

    example_cands = parse_spccl_file(test_file, 1)
    print('Number of example candidates: {0}'.format(len(example_cands)))

    # benchmark on increasing numbers of synthetic candidates
    for ncands in [5000, 10000, 50000, 100000, 200000]:
        # generate larger synthetic data set from example candidates
        # pick candidates with replacement
        idx = np.random.choice(
            example_cands.shape[0],
            ncands,
            replace=True
        )

        candidates = example_cands[idx]

        # generate correct indices so that the clusterer works
        # each input candidate needs to have a unique index
        candidates['index'] = np.arange(len(candidates))

        print('Number of synthetic candidates: {0}'.format(len(candidates)))

        clust = Clusterer()

        with MyTimer() as timer:
            clust.match_candidates(candidates)

        print('Runtime: {0:.1f} s'.format(timer.runtime))
        print('Clustering rate: {0:.1f} candidates/s'.format(
            ncands / timer.runtime
            )
        )


if __name__ == "__main__":
    main()
