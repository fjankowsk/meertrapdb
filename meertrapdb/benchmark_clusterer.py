# coding: utf-8
#
#   Benchmark the multi-beam clusterer.
#   2020 Fabian Jankowski
#

import os.path
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from meertrapdb.clustering.clusterer import Clusterer
from meertrapdb.parsing_helpers import parse_spccl_file


class MyTimer:
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

        msg = "The function took: {0:.3f} s.".format(self.runtime)
        print(msg)


def plot_runtime_scaling(df):
    """
    Plot the runtime scaling.

    Parameters
    ----------
    df: ~pd.DataFrame
        The input data.
    """

    fig = plt.figure()
    ax = fig.add_subplot(111)

    plot_range = np.geomspace(np.min(df["ncands"]), np.max(df["ncands"]), num=100)

    ax.plot(df["ncands"], df["runtime"], marker="o", label="measured")

    ax.plot(plot_range, 4.0e-7 * plot_range**1.6, label=r"$T(n) \propto n^{1.6}$")

    ax.grid()
    ax.legend(loc="best", frameon=False)
    ax.set_xlabel("Number of candidates")
    ax.set_ylabel("Runtime (s)")
    ax.set_xscale("log")
    ax.set_yscale("log")

    fig.tight_layout()

    fig.savefig("clusterer_runtime_scaling.pdf", bbox_inches="tight")

    plt.close(fig)


#
# MAIN
#


def main():
    test_file = os.path.join(
        os.path.dirname(__file__), "tests", "test_clusterer_candidates.spccl.log"
    )

    example_cands = parse_spccl_file(test_file, 1)
    print("Number of example candidates: {0}".format(len(example_cands)))

    df = pd.DataFrame(columns=["ncands", "runtime"])

    # benchmark on increasing numbers of synthetic candidates
    for ncands in [5000, 10000, 25000, 50000, 100000, 200000]:
        # generate larger synthetic data set from example candidates
        # pick candidates with replacement
        idx = np.random.choice(example_cands.shape[0], ncands, replace=True)

        candidates = example_cands[idx]

        # generate correct indices so that the clusterer works
        # each input candidate needs to have a unique index
        candidates["index"] = np.arange(len(candidates))

        print("Number of synthetic candidates: {0}".format(len(candidates)))

        clust = Clusterer()

        with MyTimer() as timer:
            clust.match_candidates(candidates)

        print("Runtime: {0:.1f} s".format(timer.runtime))
        print("Clustering rate: {0:.1f} candidates/s".format(ncands / timer.runtime))

        temp = {"ncands": ncands, "runtime": timer.runtime}

        df = df.append(temp, ignore_index=True)

    print(df.to_string())

    plot_runtime_scaling(df)


if __name__ == "__main__":
    main()
