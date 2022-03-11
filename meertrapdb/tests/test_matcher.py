#
#   2020 - 2021 Fabian Jankowski
#

from io import StringIO
import os.path
import pickle

from astropy.coordinates import Angle, SkyCoord
import astropy.units as units
import numpy as np
from numpy.testing import assert_raises
import pandas as pd

from psrmatch.matcher import Matcher

# astropy generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def test_catalogue_loading():
    m = Matcher()

    # simple loading
    m.load_catalogue("psrcat")

    np.testing.assert_equal(m.loaded_catalogues, ["psrcat"])

    # double loading
    with assert_raises(RuntimeError):
        m.load_catalogue("psrcat")

    # unknown catalogue
    with assert_raises(NotImplementedError):
        m.load_catalogue("blablabla")


def test_catalogue_unloading():
    m = Matcher()

    np.testing.assert_equal(m.loaded_catalogues, [])

    m.load_catalogue("psrcat")

    m.unload_catalogues()

    np.testing.assert_equal(m.loaded_catalogues, [])


def test_matcher_readiness():
    m = Matcher()

    coords = SkyCoord(
        ra="08:35:20", dec="-45:10:34", unit=(units.degree, units.degree), frame="icrs"
    )

    dm = 67.97

    # not prepared
    with assert_raises(RuntimeError):
        m.find_matches(coords, dm)

    # working
    m.load_catalogue("psrcat")
    m.create_search_tree()

    m.find_matches(coords, dm)


def test_psrcat_matches():
    # known good output
    good_filename = os.path.join(
        os.path.dirname(__file__), "test_matcher_good_data.pkl"
    )

    if os.path.isfile(good_filename):
        with open(good_filename, "rb") as fd:
            known_good = pickle.load(fd)

    else:
        # generate fake sources
        print("Generate fake sources.")

        nsource = 10000

        # generate random parameters
        ras = np.random.uniform(0, 360, size=nsource)
        decs = np.random.uniform(-90, 25, size=nsource)
        dms = np.random.uniform(3, 1000, size=nsource)

        known_good = {"ras": ras, "decs": decs, "dms": dms}

    # parse coordinates
    coords = SkyCoord(
        ra=known_good["ras"],
        dec=known_good["decs"],
        unit=(units.degree, units.degree),
        frame="icrs",
    )

    # prepare matcher
    m = Matcher()
    m.load_catalogue("psrcat")
    m.create_search_tree()

    matches = []

    for source, dm in zip(coords, known_good["dms"]):
        match = m.find_matches(source, dm)
        matches.append(match)

    if os.path.isfile(good_filename):
        np.testing.assert_equal(matches, known_good["matches"])

    else:
        known_good = {"ras": ras, "decs": decs, "dms": dms, "matches": matches}

        with open(good_filename, "wb") as fd:
            pickle.dump(known_good, fd, pickle.DEFAULT_PROTOCOL)


def test_psrcat_trivial_matches():
    # trivially match psrcat pulsars against themselves

    m = Matcher()
    m.load_catalogue("psrcat")
    m.create_search_tree()

    coords = SkyCoord(
        ra=m.catalogue["ra"],
        dec=m.catalogue["dec"],
        unit=(units.degree, units.degree),
        frame="icrs",
    )

    for item, coord in zip(m.catalogue, coords):
        match = m.find_matches(coord, item["dm"])

        assert match is not None

        # treat the double pulsar and pulsars in globular clusters
        if match["psrj"][-1].isdigit():
            assert match["psrj"] == item["psrj"]


def test_psrcat_spatial_offsets():
    # match psrcat pulsars shifted in position against psrcat
    # no shift in catalogue dms is performed though

    m = Matcher()
    m.load_catalogue("psrcat")
    m.create_search_tree()

    separation = (m.dist_thresh - 0.01) * units.deg

    for item in m.catalogue:
        psrcoord = SkyCoord(
            ra=item["ra"], dec=item["dec"], unit=(units.deg, units.deg), frame="icrs"
        )

        for pa in [0, 90, 180, 270]:
            coord = psrcoord.directional_offset_by(pa * units.deg, separation)

            match = m.find_matches(coord, item["dm"])
            if match is None:
                print(coord, item, psrcoord.separation(coord).deg)
            else:
                if match["psrj"] != item["psrj"]:
                    print(item["psrj"], match["psrj"])
            # assert(match['psrj'] == item['psrj'])
            # assert(match is not None)


def test_psrcat_dm_offsets():
    # match psrcat pulsars at original position just shifted in dm

    m = Matcher()
    m.load_catalogue("psrcat")
    m.create_search_tree()

    offset = Angle(m.dist_thresh - 0.01, unit=units.degree)

    for item in m.catalogue:
        for fact in [-1, 1]:
            dm = item["dm"] * (1 + fact * (m.dm_thresh - 1.0) / 100.0)

            coord = SkyCoord(
                ra=item["ra"],
                dec=item["dec"],
                unit=(units.degree, units.degree),
                frame="icrs",
            )
            match = m.find_matches(coord, dm)

            assert match is not None

            # treat the double pulsar and pulsars in globular clusters
            if match["psrj"][-1].isdigit():
                assert match["psrj"] == item["psrj"]


def test_ib_candidates():
    # test if ib candidates match correctly against bright pulsar

    candidates_str = """ra,dec,dm
14h59m54.01s,-64d27m06.3s,71.22400
14h59m54.01s,-64d27m06.3s,70.91700
14h59m54.01s,-64d27m06.3s,70.61000
14h59m54.01s,-64d27m06.3s,71.53100
14h59m54.01s,-64d27m06.3s,71.83800
14h59m54.01s,-64d27m06.3s,72.14500
"""

    df = pd.read_csv(StringIO(candidates_str), header="infer")

    m = Matcher()
    m.load_catalogue("psrcat")
    m.create_search_tree()

    for i in range(len(df.index)):
        item = df.loc[i]

        coord = SkyCoord(
            ra=item["ra"],
            dec=item["dec"],
            frame="icrs",
            unit=(units.hourangle, units.deg),
        )

        matches = m.find_matches(coord, item["dm"])

        assert matches is not None
        assert matches["psrj"] == "J1453-6413"


def test_private_access():
    m = Matcher()

    with assert_raises(AttributeError):
        m.__dist_thresh

    with assert_raises(AttributeError):
        m.__dm_thresh


def test_parameter_access():
    m = Matcher(1.5, 5.0)

    assert m.dist_thresh == 1.5
    assert m.dm_thresh == 0.05


def test_parameter_change():
    m = Matcher(1.5, 5.0)

    m.dist_thresh = 3.0
    m.dm_thresh = 15.0

    assert m.dist_thresh == 3.0
    assert m.dm_thresh == 0.15


def test_invalid_parameters():
    m = Matcher(1.5, 5.0)

    with assert_raises(RuntimeError):
        m.dist_thresh = -20.0

    with assert_raises(RuntimeError):
        m.dm_thresh = "bla"

    assert m.dist_thresh == 1.5
    assert m.dm_thresh == 0.05


if __name__ == "__main__":
    import nose2

    nose2.main()
