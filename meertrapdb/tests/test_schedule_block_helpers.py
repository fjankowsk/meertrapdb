# -*- coding: utf-8 -*-
#
#   2020 Fabian Jankowski
#

import os.path

from meertrapdb.schedule_block_helpers import get_sb_info


def test_get_sb_info():
    # keys that must exist
    keys = [
        'actual_start_time',
        'id',
        'id_code',
        'proposal_id',
        'sub_nr',
        'owner',
        'description'
        'antennas_alloc'
    ]

    for version in [1, 2]:
        sb_info = get_sb_info(version)
        print('Parsed SB info version: {0}'.format(version))

        for key in keys:
            if key in sb_info:
                pass


if __name__ == '__main__':
    import nose2
    nose2.main()
