# coding: utf-8
#
#   Test healpy functionality.
#   2020 Fabian Jankowski
#

import numpy as np
import healpy as hp


for expon in range(6, 20):
    iside = 2**expon 
    print('{0:6} {1:8.1f}'.format(iside, 60 * hp.nside2resol(iside, arcmin=True)))
