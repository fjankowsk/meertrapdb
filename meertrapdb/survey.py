#
#   2022 Fabian Jankowski
#   Survey-related helper code.
#

import glob
import os.path

from astropy import units
from astropy.coordinates import Angle, SkyCoord
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def get_cfreq_data():
    """
    Get the centre frequency information.

    Returns
    -------
    df: ~pandas.DataFrame
        The centre frequency data.
    """

    files = glob.glob("fbfuse_sensor_dump/*_centre_frequency_*.csv")
    files = sorted(files)

    if not len(files) > 0:
        raise RuntimeError("Need to provide input files.")

    frames = []

    for item in files:
        names = ["name", "sample_ts", "value_ts", "status", "value"]

        temp = pd.read_csv(item, comment="#", names=names, quotechar='"')
        frames.append(temp)

    df = pd.concat(frames, ignore_index=True, sort=False)

    # sort
    df = df.sort_values(by="sample_ts")
    df.index = range(len(df.index))

    # convert to dates
    df["date"] = pd.to_datetime(df["sample_ts"], unit="s")

    # convert to numeric
    df["value"] = df["value"].apply(pd.to_numeric)

    # treat empty values
    mask = df["value"] == 0
    df.loc[mask, "value"] = np.nan

    return df


def match_observing_bands(df):
    """
    Match the observations to observing bands.

    Parameters
    ----------
    df: ~pd.DataFrame
        The observation data.

    Returns
    -------
    df: ~pd.DataFrame
        The observation data with bands included.
    """

    df_cfreq = get_cfreq_data()

    fudge = pd.to_timedelta(600.0, unit="s")
    bands = []

    for i in range(len(df)):
        band = ""

        if np.isnan(df.at[i, "tobs"]):
            pass
        else:
            # search in a window of +- 10 min around the obs including tobs
            start = df.at[i, "date"] - fudge
            end = df.at[i, "date"] + pd.to_timedelta(df.at[i, "tobs"], unit="s") + fudge
            # print('Start, end: {0}, {1}'.format(start, end))

            mask = (
                (df_cfreq["date"] >= start)
                & (df_cfreq["date"] <= end)
                & np.isfinite(df_cfreq["value"])
            )
            sel = df_cfreq.loc[mask]

            # print(len(sel))

            if len(sel) > 0:
                # use the most common value and convert to ghz
                cfreq = sel["value"].mode().iat[0] / 1.0e9

                if 0 < cfreq < 1.0:
                    band = "u"
                elif 1.0 < cfreq < 2.0:
                    band = "l"
                elif cfreq > 2.0:
                    band = "s"
                else:
                    raise RuntimeError("Band unknown: {0}".format(cfreq))

        bands.append(band)

    df["band"] = bands

    return df


def plot_galactic_latitude_bins(t_df):
    """
    Plot the exposure in Galactic latitude bins.

    Parameters
    ----------
    t_df: ~pd.DataFrame
        The pointing data.
    """

    df = t_df.copy()

    # work out exposure in galactic latitude bins
    mask = np.logical_not(df["tobs"].isnull())
    sel = df[mask].copy()

    coords = SkyCoord(
        ra=sel["ra"], dec=sel["dec"], unit=(units.deg, units.deg), frame="icrs"
    )

    gbs = coords.galactic.b.value

    # galactic latitude thresholds
    lats = np.linspace(-90, 90, num=26)
    step = np.diff(lats)[0]

    print("Latitudes: {0}".format(lats))
    print("Step: {0:.2f} deg".format(step))

    df_lat = pd.DataFrame(columns=["lat_lo", "lat_hi", "lat_mid", "tobs", "pointings"])

    for i in range(len(lats) - 1):
        lat_lo = lats[i]
        lat_hi = lats[i + 1]

        mask = (gbs >= lat_lo) & (gbs < lat_hi)

        df_lat.at[i, "lat_lo"] = lat_lo
        df_lat.at[i, "lat_hi"] = lat_hi
        df_lat.at[i, "lat_mid"] = 0.5 * (lat_lo + lat_hi)
        df_lat.at[i, "tobs"] = sel.loc[mask, "tobs"].sum()
        df_lat.at[i, "pointings"] = len(sel[mask])

    # convert object to numeric
    df_lat = df_lat.apply(pd.to_numeric)

    print(df_lat.info())
    print(df_lat.to_string())

    # sanity check
    assert df_lat["tobs"].sum() == sel["tobs"].sum()

    df_lat.to_pickle("tobs_vs_gb.pkl")

    fig = plt.figure()
    ax = fig.add_subplot(111)

    edges = np.append(
        df_lat["lat_lo"].to_numpy(),
        df_lat["lat_hi"].iloc[-1],
    )

    ax.stairs(
        values=df_lat["tobs"] / 86400.0,
        edges=edges,
        color="black",
        lw=2.0,
        zorder=4,
    )

    ax.grid()
    ax.set_xlabel("Gb (deg)")
    ax.set_ylabel("Observing time (d)")

    fig.tight_layout()

    fig.savefig("tobs_vs_gb.pdf", dpi=300)


def query_source_exposure(m, t_df):
    """
    Query and plot the exposure of sources.

    Parameters
    ----------
    m: ~meetrapdb.Skymap
        The skymap to query.
    t_df: ~pd.DataFrame
        The source data.
    """

    df_sources = t_df.copy()

    # query the exposure of the detections
    coords = SkyCoord(
        ra=df_sources["ra"],
        dec=df_sources["dec"],
        unit=(units.hourangle, units.deg),
        frame="icrs",
    )

    exposures = m.query(coords, [0.1 for _ in range(len(coords))])

    df_sources["tobs"] = exposures

    print(df_sources.to_string(columns=["name", "tobs"]))

    # exposure time histogram
    fig = plt.figure()
    ax = fig.add_subplot(111)

    _, bins, _ = ax.hist(
        df_sources["tobs"], histtype="step", bins=40, color="black", lw=1.5, zorder=3
    )

    for item in np.unique(df_sources["type"]):
        mask = df_sources["type"] == item
        sel = df_sources.loc[mask]

        ax.hist(sel["tobs"], histtype="step", bins=bins, lw=2, zorder=4, label=item)

    ax.grid()
    ax.set_xlabel("tobs (h)")
    ax.set_ylabel("Number")
    ax.set_title("Source exposure")
    ax.legend(loc="best", frameon=False)

    fig.tight_layout()

    fig.savefig("exposure_hist.png", dpi=300)


def plot_exposure_timeline(t_df_sources, t_df, coords, radius=0.75):
    """
    Plot an exposure timeline for a given source.

    Parameters
    ----------
    t_df_sources: ~pd.DataFrame
        The source data.
    t_df: ~pd.DataFrame
        The exposure data.
    coords: ~astropy.SkyCoord
        The coordinates of the pointing centres.
    radius: float
        The separation radius to consider for matches.
    """

    df_sources = t_df_sources.copy()
    df = t_df.copy()

    coords_sources = SkyCoord(
        ra=df_sources["ra"],
        dec=df_sources["dec"],
        unit=(units.hourangle, units.deg),
        frame="icrs",
    )

    for i in range(len(df_sources)):
        mask = coords.separation(coords_sources[i]) < Angle(radius * units.deg)

        sel = df[mask].copy()
        sel.index = range(len(sel))

        fig = plt.figure()
        ax = fig.add_subplot(111)

        ax.scatter(
            sel["date"],
            np.ones(len(sel.index)),
            marker="o",
            color="C0",
            zorder=4,
        )

        ax.grid()
        ax.set_xlabel("Date")

        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 7)))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%b"))

        ax.set_title(df_sources["name"].iat[i])

        fig.tight_layout()


def remove_bad_pointings(t_df):
    """
    Remove pointings where the pipeline was not working as expected.
    """

    df = t_df.copy()

    bad_pointings_fn = os.path.join(
        os.path.dirname(__file__), "..", "config", "bad_pointings_ib.csv"
    )
    bad_pointings_fn = os.path.abspath(bad_pointings_fn)

    df_bad = pd.read_csv(bad_pointings_fn, comment="#", names=["start", "end"], sep=",")

    # convert to dates
    df_bad["start"] = pd.to_datetime(df_bad["start"])
    df_bad["end"] = pd.to_datetime(df_bad["end"])

    df_bad.info()
    print(df_bad.to_string())

    print("Entries before bad pointings removal: {0}".format(len(df.index)))

    for i in range(len(df_bad.index)):
        start = df_bad.at[i, "start"]
        end = df_bad.at[i, "end"]
        # print('Start, end: {0}, {1}'.format(start, end))

        mask = (df["date"] >= start) & (df["date"] < end)
        mask = np.logical_not(mask)

        df = df[mask]

    df.index = range(len(df.index))
    print("Entries after bad pointings removal: {0}".format(len(df.index)))

    return df
