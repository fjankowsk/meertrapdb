# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path

from meertrapdb.parsing_helpers import parse_spccl_file


def test_spccl_versions_parsing():
    cand_v1 = os.path.join(os.path.dirname(__file__), "candidates_v1.spccl.log")

    cand_v2 = os.path.join(os.path.dirname(__file__), "candidates_v2.spccl.log")

    for filename, version in zip([cand_v1, cand_v2], [1, 2]):
        print("Filename: {0}".format(filename))
        print("Version: {0}".format(version))
        parse_spccl_file(filename, version)


if __name__ == "__main__":
    import nose2

    nose2.main()
