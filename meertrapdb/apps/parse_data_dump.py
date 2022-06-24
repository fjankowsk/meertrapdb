#
#   2021 Fabian Jankowski
#   Process the sensor data dump.
#

import argparse
import glob
import os.path
import sys

from astropy import units
from astropy.coordinates import SkyCoord
import katpoint
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from meertrapdb.config_helpers import get_config
from meertrapdb import plotting, survey
from skymap import Skymap

# astropy.units generates members dynamically, pylint therefore fails
# disable the corresponding pylint test for now
# pylint: disable=E1101


def parse_args():
    """
    Parse the commandline arguments.

    Returns
    -------
    args: populated namespace
        The commandline arguments.
    """

    parser = argparse.ArgumentParser(
        description="Process the sensor data dump.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--enddate",
        dest="enddate",
        type=str,
        metavar=("YYYY-MM-DDThh:mm:ss"),
        help="Process sensor data until this UTC date in ISOT format.",
    )

    return parser.parse_args()


def run_timeline():
    """
    Run the processing for timeline mode.
    """

    files = glob.glob("fbfuse*.csv")
    files = sorted(files)

    frames = []

    for item in files:
        names = ["name", "sample_ts", "value_ts", "status", "value"]

        temp = pd.read_csv(item, comment="#", names=names, quotechar='"')

        frames.append(temp)

    df = pd.concat(frames, ignore_index=True, sort=False)

    # convert to dates
    df["date"] = pd.to_datetime(df["sample_ts"], unit="s")

    # add unit field
    df["unit"] = ""

    # convert to mhz
    mask = np.logical_or(
        df["name"] == "fbfuse_1_fbfmc_array_1_bandwidth",
        df["name"] == "fbfuse_1_fbfmc_array_1_centre_frequency",
    )
    df.loc[mask, "value"] = df.loc[mask, "value"] * 1e-6
    df.loc[mask, "unit"] = "MHz"

    # add unit
    mask = df["name"] == "fbfuse_1_fbfmc_array_1_coherent_beam_count"
    df.loc[mask, "unit"] = "#"

    print(df.info())
    print(np.unique(df["name"]))

    fig, axs = plt.subplots(
        nrows=len(np.unique(df["name"])), ncols=1, sharex=True, sharey=False
    )

    for i, item in enumerate(np.unique(df["name"])):
        print("Plotting: {0}".format(item))

        mask = df["name"] == item
        sel = df.loc[mask]

        axs[i].scatter(
            sel["date"], sel["value"], color="C0", marker=".", s=4, label=item, zorder=3
        )

        axs[i].grid()
        axs[i].set_ylabel("({0})".format(sel.at[0, "unit"]))
        axs[i].legend(loc="best", frameon=False)

    axs[-1].set_xlabel("UTC")

    fig.tight_layout()

    fig.savefig("timeline.png", dpi=300)


def run_ib_pointing(params):
    """
    Run the processing for IB pointing mode.

    Parameters
    ----------
    params: dict
        Additional parameters for the processing.
    """

    files = glob.glob("fbfuse_sensor_dump/*_phase_reference_*.csv")
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

    # parse targets
    df["value"] = df["value"].str.strip('"')

    coords = []

    for i in range(len(df)):
        raw = df.at[i, "value"]

        name = ""
        ra = np.nan
        dec = np.nan

        try:
            target = katpoint.Target(raw)
            name = target.name
            result = target.astrometric_radec()
            ra = np.degrees(result[0])
            dec = np.degrees(result[1])
        except Exception:
            pass

        coords.append([name, ra, dec])

    df["name"] = [item[0] for item in coords]
    df["ra"] = [item[1] for item in coords]
    df["dec"] = [item[2] for item in coords]

    # add observing time
    df["tobs"] = df["sample_ts"].diff()

    mask = (
        (df["name"] == "")
        | (df["name"] == "unset")
        | (df["ra"] == 0)
        | (df["dec"] == 0)
        | df["ra"].isnull()
        | df["dec"].isnull()
    )

    df.loc[mask, "tobs"] = np.nan

    # remove short bogus pointings
    mask = df["tobs"] < 60.0
    df.loc[mask, "tobs"] = np.nan

    # remove pointings at the end of a session
    mask = df["tobs"] > 3600.0
    df.loc[mask, "tobs"] = np.nan

    # truncate (incorrect) long pointings
    mask = df["tobs"] > 700.0
    df.loc[mask, "tobs"] = 600.0

    df.info()
    # print(df.to_string(columns=['name', 'ra', 'dec', 'tobs']))

    # consider only data until end date
    if "enddate" in params and params["enddate"] is not None:
        mask = df["date"] <= params["enddate"]
        df = df[mask]

    # remove pointings where the pipeline was not working as expected
    bad_pointings_fn = os.path.join(
        os.path.dirname(__file__), "..", "config", "bad_pointings_ib.csv"
    )
    bad_pointings_fn = os.path.abspath(bad_pointings_fn)

    df_bad = pd.read_csv(bad_pointings_fn, comment="#", names=["start", "end"], sep=",")

    # convert to dates
    df_bad["start"] = pd.to_datetime(df_bad["start"], infer_datetime_format=True)
    df_bad["end"] = pd.to_datetime(df_bad["end"], infer_datetime_format=True)

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

    # plot tobs
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(df["date"], df["tobs"], marker=".", color="black", s=0.5, zorder=3)

    ax.grid()
    ax.set_xlabel("MJD")
    ax.set_ylabel("tobs (s)")

    fig.tight_layout()

    fig.savefig("tobs_timeline.png", dpi=300)

    # histogram of tobs
    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.hist(df["tobs"], histtype="step", bins=30, color="black", lw=1.5, zorder=3)

    ax.grid()
    ax.set_xlabel("tobs (s)")
    ax.set_ylabel("Number")

    fig.tight_layout()

    fig.savefig("tobs_hist.png", dpi=300)

    # figure out observing band
    df = survey.match_observing_bands(df)
    # print(df.to_string(columns=["name", "date", "tobs", "band", "status", "value"]))

    # add exposure to sky map
    config = get_config()
    smconfig = config["skymap"]
    nside = smconfig["nside"]
    quantity = smconfig["quantity"]
    unit = smconfig["unit"]

    m = Skymap(nside=nside, quantity=quantity, unit=unit)

    mask = np.logical_not(df["tobs"].isnull())
    sel = df[mask].copy()

    print(
        "Total time span: {0:.1f} days".format(
            (sel["date"].max() - sel["date"].min()).total_seconds() / 86400.0
        )
    )

    print("Total tobs: {0:.1f} days".format(sel["tobs"].sum() / 86400.0))

    for band in sel["band"].unique():
        mask = sel["band"] == band
        sel2 = sel[mask]

        print(
            "Fraction {0}-band: {1:.2f} %".format(
                band.upper(), 100 * sel2["tobs"].sum() / sel["tobs"].sum()
            )
        )

    print(
        "Average observing time: {0:.2f} hours / day".format(
            24
            * sel["tobs"].sum()
            / (sel["date"].max() - sel["date"].min()).total_seconds()
        )
    )

    coords = SkyCoord(
        ra=sel["ra"], dec=sel["dec"], unit=(units.deg, units.deg), frame="icrs"
    )

    # add primary beam radii
    # use the circle equivalent ones for given area
    pb_radius_l = np.sqrt(smconfig["beam_area"]["l_band"]["pb"] / np.pi)
    pb_radius_u = np.sqrt(smconfig["beam_area"]["uhf_band"]["pb"] / np.pi)

    # use l-band as default
    sel["radius"] = pb_radius_l

    mask = sel["band"] == "l"
    sel.loc[mask, "radius"] = pb_radius_l

    mask = sel["band"] == "u"
    sel.loc[mask, "radius"] = pb_radius_u

    m.add_exposure(coords, sel["radius"], sel["tobs"] / 3600.0)

    # add start/end time meta data
    m.add_comment("Start UTC: {0}".format(sel["date"].min()))
    m.add_comment("End UTC: {0}".format(sel["date"].max()))

    print("Start UTC: {0}".format(sel["date"].min()))
    print("End UTC: {0}".format(sel["date"].max()))
    print("Start Unix epoch: {0}".format(sel["sample_ts"].min()))
    print("End Unix epoch: {0}".format(sel["sample_ts"].max()))

    print("Fraction of the map covered: {0:.4f}".format(m.fraction_covered))

    # compute l-band survey coverage, i.e. sum area x tobs
    mask = sel["band"] == "l"
    sel2 = sel[mask].copy()

    tot_tobs = np.sum((sel2["tobs"] / 3600.0))
    inco_cover = tot_tobs * smconfig["beam_area"]["l_band"]["pb"]
    co_cover = tot_tobs * smconfig["beam_area"]["l_band"]["cb"]
    print("L-band Incoherent survey coverage: {0:.2f} deg^2 hr".format(inco_cover))
    print("L-band Coherent survey coverage: {0:.2f} deg^2 hr".format(co_cover))

    # m.save_to_file('skymap_from_data_dump.pkl')
    print(m)

    # plot discoveries
    source_file = "sources.csv"
    if os.path.isfile(source_file):
        df_sources = pd.read_csv(source_file, sep=",", comment="#", header="infer")
        survey.query_source_exposure(m, df_sources)
    else:
        df_sources = None

    params = {"shownames": True, "fontsize": "small", "markersize": 80}

    m.show(coordinates="galactic", sources=df_sources, params=params)
    m.show(coordinates="equatorial", sources=df_sources, params=params)

    survey.plot_galactic_latitude_bins(df)


def run_cb_pointing(params):
    """
    Run the processing for CB pointing mode.

    Parameters
    ----------
    params: dict
        Additional parameters for the processing.
    """

    # create sky map
    config = get_config()
    smconfig = config["skymap"]

    m = Skymap(nside=smconfig["nside"], quantity=smconfig["quantity"], unit="a.u.")

    files = glob.glob("fbfuse_sensor_dump/*_array_1_coherent_beam_cfbf00[0-7]??_*.csv")
    files = sorted(files)

    if not len(files) > 0:
        raise RuntimeError("Need to provide input files.")

    print("Number of files to process: {0}".format(len(files)))

    # use the circle equivalent ones for given area
    cb_radius_l = np.sqrt(smconfig["beam_area"]["l_band"]["cb"] / (768.0 * np.pi))
    print("Half-power CB radius: {0:.4f} deg".format(cb_radius_l))

    names = ["name", "sample_ts", "value_ts", "status", "value"]

    for ifile, item in enumerate(files):
        print("{0:<8} {1}".format(ifile, item))
        df = pd.read_csv(item, comment="#", names=names, quotechar='"')

        # convert to dates
        df["date"] = pd.to_datetime(df["sample_ts"], unit="s")

        # parse targets
        df["value"] = df["value"].str.strip('"')

        coords = []

        for i in range(len(df)):
            raw = df.at[i, "value"]

            name = ""
            ra = np.nan
            dec = np.nan

            try:
                target = katpoint.Target(raw)
                name = target.name
                result = target.astrometric_radec()
                ra = np.degrees(result[0])
                dec = np.degrees(result[1])
            except Exception:
                pass

            coords.append([name, ra, dec])

        df["name"] = [item[0] for item in coords]
        df["ra"] = [item[1] for item in coords]
        df["dec"] = [item[2] for item in coords]

        # add observing time
        df["tobs"] = df["sample_ts"].diff()

        mask = (
            (df["name"] == "")
            | (df["name"] == "unset")
            | (df["ra"] == 0)
            | (df["dec"] == 0)
            | df["ra"].isnull()
            | df["dec"].isnull()
        )

        df.loc[mask, "tobs"] = np.nan

        mask = np.logical_not(df["tobs"].isnull())
        df = df[mask]
        df.index = range(len(df.index))

        # add primary beam radii
        df["radius"] = cb_radius_l

        # df.info()
        # print(df.to_string(columns=["name", "ra", "dec", "tobs"]))

        coords = SkyCoord(
            ra=df["ra"], dec=df["dec"], unit=(units.deg, units.deg), frame="icrs"
        )

        m.add_exposure(coords, df["radius"], df["tobs"] / 3600.0)
        del df
        del coords

    m.save_to_file("skymap_coherent.pkl")
    print(m)

    m.show(coordinates="galactic")
    m.show(coordinates="equatorial")


#
# MAIN
#


def main():
    args = parse_args()

    plotting.use_custom_matplotlib_formatting()

    enddate = None

    if args.enddate is not None:
        try:
            enddate = pd.Timestamp(args.enddate)
        except ValueError as e:
            sys.exit("Input date is invalid: {0}".format(e))

    print("End date UTC: {0}".format(enddate))

    params = {"enddate": enddate}

    run_ib_pointing(params)
    # run_cb_pointing(params)

    plt.show()

    print("All done.")


if __name__ == "__main__":
    main()
