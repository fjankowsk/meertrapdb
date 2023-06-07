#
#   2023 Fabian Jankowski
#   Plot a CB timeline from the the sensor data dump.
#

import glob
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from meertrapdb import survey


def plot_timeline(t_df):
    df = t_df.copy()

    fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(
        nrows=6, ncols=1, figsize=(12, 7), sharex=True, sharey=False
    )

    ax1.scatter(df["date"], df["area"], color="black", marker=".", zorder=4)

    ax1.grid()
    ax1.set_ylabel("Area ($\mathrm{arcmin}^2$)")

    ax2.scatter(df["date"], df["nbeam"], color="black", marker=".", zorder=4)

    ax2.grid()
    ax2.set_ylabel("Nbeam")

    ax3.scatter(df["date"], df["nant_cb"], color="black", marker=".", zorder=4)

    ax3.grid()
    ax3.set_ylabel("$\mathrm{Nant}_\mathrm{cb}$")

    ax4.scatter(df["date"], df["nant_ib"], color="black", marker=".", zorder=4)

    ax4.grid()
    ax4.set_ylabel("$\mathrm{Nant}_\mathrm{ib}$")

    ax5.scatter(df["date"], df["tot_area"], color="black", marker=".", zorder=4)

    ax5.grid()
    ax5.set_ylabel("Tot_area ($\mathrm{deg}^2$)")

    ax6.scatter(df["date"], df["freq"], color="black", marker=".", zorder=4)

    ax6.grid()
    ax6.set_ylabel("Freq (MHz)")
    ax6.set_xlabel("Date")

    fig.tight_layout()


def plot_area_histogram(t_df, field):
    """
    Plot an area histogram.
    """

    df = t_df.copy()

    mask = df[field] > 0.05
    fig, (ax1, ax2) = plt.subplots(
        nrows=2, ncols=1, figsize=(6.4, 6.4), sharex=True, sharey=False
    )

    ax1.hist(
        df.loc[mask, field],
        color="black",
        bins=71,
        density=True,
        histtype="step",
        lw=2,
        zorder=4,
    )

    ax1.axvline(
        x=np.median(df.loc[mask, field]), color="gray", ls="dashed", lw=2, zorder=6
    )

    ax1.axvline(x=np.mean(df.loc[mask, field]), color="C0", ls="dotted", lw=2, zorder=6)

    print(
        "Mean, median: {0:.2f} {1:.2f} deg2".format(
            np.nanmean(df.loc[mask, field]), np.nanmedian(df.loc[mask, field])
        )
    )

    ax1.grid()
    ax1.set_ylabel("PDF")

    ax2.hist(
        df.loc[mask, field],
        color="black",
        bins=71,
        density=True,
        cumulative=True,
        histtype="step",
        lw=2,
        zorder=4,
    )

    ax2.grid()
    ax2.set_ylabel("CDF")
    ax2.set_xlabel("Area (deg2)")
    ax2.set_title("{0} area".format(field))

    fig.tight_layout()


def load_data(files):
    """
    Load the CSV data from the files.
    """

    if not len(files) > 0:
        raise RuntimeError("Need to provide input files.")

    files = sorted(files)

    print("Number of files to process: {0}".format(len(files)))

    names = ["name", "sample_ts", "value_ts", "status", "value"]

    frames = []

    for ifile, item in enumerate(files):
        print("{0:<8} {1}".format(ifile, item))
        temp_df = pd.read_csv(item, comment="#", names=names, quotechar='"')
        frames.append(temp_df)

    df = pd.concat(frames, ignore_index=True, sort=False)

    # convert to dates
    df["date"] = pd.to_datetime(df["sample_ts"], unit="s")

    return df


#
# MAIN
#


def main():
    # centre frequency
    files = glob.glob(
        "fbfuse_sensor_dump/fbfuse_1_fbfmc_array_1_centre_frequency_*.csv"
    )
    files = sorted(files)

    df = load_data(files)

    # remove nans
    mask = df["value"].notna()
    df = df[mask]
    df.index = range(len(df.index))

    df["freq"] = df["value"] * 1e-6

    # sanitise
    mask = df["freq"] > 0
    df = df[mask]
    df.index = range(len(df.index))

    # remove pointings where the pipeline was not working as expected
    df = survey.remove_bad_pointings(df)

    df.info()

    # cb beam shape
    files = glob.glob(
        "fbfuse_sensor_dump/fbfuse_1_fbfmc_array_1_coherent_beam_shape_*.csv"
    )
    files = sorted(files)

    df_shape = load_data(files)

    df_shape["value"] = df_shape["value"].str.strip('"')
    df_shape["value"] = df_shape["value"].str.replace(r'\\"', '"', regex=True)

    mask = (df_shape["value"] != "") & df_shape["value"].notna()
    df_shape = df_shape[mask]
    df_shape.index = range(len(df_shape.index))

    df_shape["x"] = np.nan
    df_shape["y"] = np.nan
    df_shape["angle"] = np.nan

    for i in range(len(df_shape.index)):
        parsed = json.loads(df_shape.loc[i, "value"])
        df_shape.loc[i, "x"] = parsed["x"]
        df_shape.loc[i, "y"] = parsed["y"]
        df_shape.loc[i, "angle"] = parsed["angle"]

    # compute area of ellipse
    df_shape["area"] = np.pi * df_shape["x"] * df_shape["y"] * 3600.0

    # sanitise
    mask = (df_shape["area"] > 0) & (df_shape["area"] <= 10.0)
    df_shape = df_shape[mask]
    df_shape.index = range(len(df_shape.index))

    # nbeam
    files = glob.glob(
        "fbfuse_sensor_dump/fbfuse_1_fbfmc_array_1_coherent_beam_count_2*.csv"
    )
    files = sorted(files)

    df_beams = load_data(files)

    df_beams["nbeam"] = df_beams["value"]

    # sanitise
    mask = df_beams["nbeam"] > 0
    df_beams = df_beams[mask]
    df_beams.index = range(len(df_beams.index))

    # coherent beam antennas
    files = glob.glob(
        "fbfuse_sensor_dump/fbfuse_1_fbfmc_array_1_coherent_beam_antennas_*.csv"
    )
    files = sorted(files)

    df_cbants = load_data(files)

    # remove nans
    mask = df_cbants["value"].notna()
    df_cbants = df_cbants[mask]
    df_cbants.index = range(len(df_cbants.index))

    df_cbants["value"] = df_cbants["value"].str.strip('"')

    df_cbants["nant_cb"] = np.nan

    for i in range(len(df_cbants.index)):
        df_cbants.loc[i, "nant_cb"] = len(df_cbants.loc[i, "value"].split(","))

    # sanitise
    mask = df_cbants["nant_cb"] > 1
    df_cbants = df_cbants[mask]
    df_cbants.index = range(len(df_cbants.index))

    # incoherent beam antennas
    files = glob.glob(
        "fbfuse_sensor_dump/fbfuse_1_fbfmc_array_1_incoherent_beam_antennas_*.csv"
    )
    files = sorted(files)

    df_ibants = load_data(files)

    # remove nans
    mask = df_ibants["value"].notna()
    df_ibants = df_ibants[mask]
    df_ibants.index = range(len(df_ibants.index))

    df_ibants["value"] = df_ibants["value"].str.strip('"')

    df_ibants["nant_ib"] = np.nan

    for i in range(len(df_ibants.index)):
        df_ibants.loc[i, "nant_ib"] = len(df_ibants.loc[i, "value"].split(","))

    # sanitise
    mask = df_ibants["nant_ib"] > 1
    df_ibants = df_ibants[mask]
    df_ibants.index = range(len(df_ibants.index))

    # cross-match the data
    print("Starting to cross-match the data.")

    for field in ["area", "nbeam", "nant_cb", "nant_ib"]:
        df[field] = np.nan

    for i in range(len(df) - 1):
        mask_shape = (df.loc[i, "date"] <= df_shape["date"]) & (
            df_shape["date"] < df.loc[i + 1, "date"]
        )
        if len(df_shape[mask_shape]) > 0:
            df.loc[i, "area"] = df_shape.loc[mask_shape, "area"].iat[0]

        mask_beam = (df.loc[i, "date"] <= df_beams["date"]) & (
            df_beams["date"] < df.loc[i + 1, "date"]
        )
        if len(df_beams[mask_beam]) > 0:
            df.loc[i, "nbeam"] = df_beams.loc[mask_beam, "nbeam"].iat[0]

        mask_cbants = (df.loc[i, "date"] <= df_cbants["date"]) & (
            df_cbants["date"] < df.loc[i + 1, "date"]
        )
        if len(df_cbants[mask_cbants]) > 0:
            df.loc[i, "nant_cb"] = df_cbants.loc[mask_cbants, "nant_cb"].iat[0]

        mask_ibants = (df.loc[i, "date"] <= df_ibants["date"]) & (
            df_ibants["date"] < df.loc[i + 1, "date"]
        )
        if len(df_ibants[mask_ibants]) > 0:
            df.loc[i, "nant_ib"] = df_ibants.loc[mask_ibants, "nant_ib"].iat[0]

    print("Cross-matching done.")

    # select only our observations at l-band
    mask = (
        (df["freq"] > 1000.0)
        & (df["freq"] < 2000.0)
        & (df["nant_cb"] >= 30)
        & (df["nant_cb"] <= 48)
    )
    df = df[mask]
    df.index = range(len(df.index))

    df["tot_area"] = df["area"] * df["nbeam"] / 3600.0

    # survey coverage
    df["survey_nbeam"] = df["nbeam"]
    mask = df["survey_nbeam"] > 768
    df.loc[mask, "survey_nbeam"] = 768
    df["survey_area"] = df["area"] * df["survey_nbeam"] / 3600.0

    survey_coverage = df["survey_area"].sum() * 10.0 / 60.0
    print(
        "CB survey coverage with beam size information: {0:.1f} deg2 h".format(
            survey_coverage
        )
    )
    # add to that the data before we had beam sizes
    mask = df["date"] < pd.Timestamp("2020-04-16T10:00:00")
    add = df[mask].copy()
    add["area"] = 0.85
    add["survey_area"] = add["area"] * add["survey_nbeam"] / 3600.0
    survey_coverage += add["survey_area"].sum() * 10.0 / 60.0
    print("CB survey coverage total: {0:.1f} deg2 h".format(survey_coverage))

    # make plots
    plot_timeline(df)

    # area histogram
    mask = df["area"] > 0.01
    fig, (ax1, ax2) = plt.subplots(
        nrows=2, ncols=1, figsize=(6.4, 6.4), sharex=True, sharey=False
    )

    ax1.hist(
        df.loc[mask, "area"],
        color="black",
        bins=71,
        density=True,
        histtype="step",
        lw=2,
        zorder=4,
    )

    ax1.axvline(
        x=np.median(df.loc[mask, "area"]), color="gray", ls="dashed", lw=2, zorder=6
    )

    ax1.axvline(
        x=np.mean(df.loc[mask, "area"]), color="C0", ls="dotted", lw=2, zorder=6
    )

    print(
        "Mean, median: {0:.2f} {1:.2f} arcmin2".format(
            np.mean(df.loc[mask, "area"]), np.median(df.loc[mask, "area"])
        )
    )

    ax1.grid()
    ax1.set_ylabel("PDF")

    ax2.hist(
        df.loc[mask, "area"],
        color="black",
        bins=71,
        density=True,
        cumulative=True,
        histtype="step",
        lw=2,
        zorder=4,
    )

    ax2.grid()
    ax2.set_ylabel("CDF")
    ax2.set_xlabel("Area ($\mathrm{arcmin}^2$)")
    ax2.set_title("Single CB area")

    fig.tight_layout()

    # area histograms
    for field in ["tot_area", "survey_area"]:
        plot_area_histogram(df, field)

    # nbeam histogram
    fig = plt.figure()
    ax = fig.add_subplot()

    ax.hist(
        df_beams["nbeam"],
        color="black",
        bins=51,
        density=True,
        histtype="step",
        lw=2,
        zorder=4,
    )

    ax.grid()
    ax.set_xlabel("Nbeam")
    ax.set_ylabel("PDF")

    fig.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
