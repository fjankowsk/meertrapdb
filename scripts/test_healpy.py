# coding: utf-8
#
#   Test healpy functionality.
#   2020 Fabian Jankowski
#

import numpy as np
import healpy as hp


print(
    '{0:<6} {1:>10} {2:>12} {3:>12}'.format(
        'Expon',
        'Nside',
        'Res',
        'Npix'
    )
)

print(
    '{0:<6} {1:>10} {2:>12} {3:>12}'.format(
        '',
        '',
        '(arcsec)',
        '(Gpix)'
    )
)

for expon in range(6, 20):
    iside = 2**expon

    print('{0:<6} {1:>10} {2:>12.1f} {3:>12.1f}'.format(
        expon,
        iside,
        60 * hp.nside2resol(iside, arcmin=True),
        hp.nside2npix(iside) * 1E-9
        )
    )

npix = hp.nside2npix(2**13)
print('Number of pixels: {0:.1f} Gpix'.format(npix * 1E-9))

print('Array size in memory')
for expon in range(12, 16):
    test = np.arange(2**expon, dtype='float')

    print('{0:<6} {1:8.1f} MB'.format(
        expon,
        test.nbytes / (1024^2)
        )
    )
