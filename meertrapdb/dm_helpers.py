#
#   2020 Fabian Jankowski
#   Milky Way DM related helper functions.
#

import pygedm


def get_mw_dm(gl, gb):
    """
    Determine the Galactic Milky Way contribution to the dispersion measure
    for a given sightline.

    We compute the mean value reported by the NE2001 and YMW16 models.

    Parameters
    ----------
    gl: float
        Galactic longitude in degrees.
    gb: float
        Galactic latitude in degrees.

    Returns
    -------
    mean_dm: float
        The mean Milky Way DM.
    """

    # 30 kpc
    dist = 30 * 1000

    dm_ne2001, _ = pygedm.dist_to_dm(gl, gb, dist, mode="gal", method="ne2001")
    dm_ymw16, _ = pygedm.dist_to_dm(gl, gb, dist, mode="gal", method="ymw16")

    mean_dm = 0.5 * (dm_ne2001 + dm_ymw16)

    return mean_dm.value
