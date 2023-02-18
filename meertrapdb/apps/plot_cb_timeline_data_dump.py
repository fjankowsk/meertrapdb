import glob
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


#
# MAIN
#


def main():
    files = glob.glob(
        "fbfuse_sensor_dump/fbfuse_1_fbfmc_array_1_coherent_beam_shape_*.csv"
    )
    files = sorted(files)

    if not len(files) > 0:
        raise RuntimeError("Need to provide input files.")

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

    df["value"] = df["value"].str.strip('"')
    df["value"] = df["value"].str.replace(r'\\"', '"', regex=True)

    mask = df["value"] != ""
    df = df[mask]
    df.index = range(len(df.index))

    df["x"] = np.nan
    df["y"] = np.nan
    df["angle"] = np.nan

    for i in range(len(df.index)):
        parsed = json.loads(df.loc[i, "value"])
        df.loc[i, "x"] = parsed["x"]
        df.loc[i, "y"] = parsed["y"]
        df.loc[i, "angle"] = parsed["angle"]

    # compute area of ellipse
    df["area"] = np.pi * df["x"] * df["y"] * 3600.0

    # sanitise
    mask = (df["area"] > 0) & (df["area"] <= 10.0)
    df = df[mask]
    df.index = range(len(df.index))

    files = glob.glob(
        "fbfuse_sensor_dump/fbfuse_1_fbfmc_array_1_coherent_beam_count_2*.csv"
    )
    files = sorted(files)

    if not len(files) > 0:
        raise RuntimeError("Need to provide input files.")

    print("Number of files to process: {0}".format(len(files)))

    names = ["name", "sample_ts", "value_ts", "status", "value"]

    frames = []

    for ifile, item in enumerate(files):
        print("{0:<8} {1}".format(ifile, item))
        temp_df = pd.read_csv(item, comment="#", names=names, quotechar='"')
        frames.append(temp_df)

    df_beams = pd.concat(frames, ignore_index=True, sort=False)

    # convert to dates
    df_beams["date"] = pd.to_datetime(df_beams["sample_ts"], unit="s")

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

    if not len(files) > 0:
        raise RuntimeError("Need to provide input files.")

    print("Number of files to process: {0}".format(len(files)))

    names = ["name", "sample_ts", "value_ts", "status", "value"]

    frames = []

    for ifile, item in enumerate(files):
        print("{0:<8} {1}".format(ifile, item))
        temp_df = pd.read_csv(item, comment="#", names=names, quotechar='"')
        frames.append(temp_df)

    df_cbants = pd.concat(frames, ignore_index=True, sort=False)

    # convert to dates
    df_cbants["date"] = pd.to_datetime(df_cbants["sample_ts"], unit="s")

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

    if not len(files) > 0:
        raise RuntimeError("Need to provide input files.")

    print("Number of files to process: {0}".format(len(files)))

    names = ["name", "sample_ts", "value_ts", "status", "value"]

    frames = []

    for ifile, item in enumerate(files):
        print("{0:<8} {1}".format(ifile, item))
        temp_df = pd.read_csv(item, comment="#", names=names, quotechar='"')
        frames.append(temp_df)

    df_ibants = pd.concat(frames, ignore_index=True, sort=False)

    # convert to dates
    df_ibants["date"] = pd.to_datetime(df_ibants["sample_ts"], unit="s")

    df_ibants["value"] = df_ibants["value"].str.strip('"')

    df_ibants["nant_ib"] = np.nan

    for i in range(len(df_ibants.index)):
        df_ibants.loc[i, "nant_ib"] = len(df_ibants.loc[i, "value"].split(","))

    # sanitise
    mask = df_ibants["nant_ib"] > 1
    df_ibants = df_ibants[mask]
    df_ibants.index = range(len(df_ibants.index))

    # compute total area
    df["tot_area"] = np.nan

    for i in range(len(df) - 1):
        mask = (df.loc[i, "date"] <= df_beams["date"]) & (
            df_beams["date"] < df.loc[i + 1, "date"]
        )
        if len(df_beams[mask]) > 0:
            nbeam = df_beams.loc[mask, "nbeam"].iat[0]
        else:
            nbeam = np.nan

        df.loc[i, "tot_area"] = df.loc[i, "area"] * nbeam / 3600.0

    # make plots
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(
        nrows=5, ncols=1, figsize=(12, 7), sharex=True, sharey=False
    )

    ax1.scatter(df["date"], df["area"], color="black", marker=".", zorder=4)

    ax1.grid()
    ax1.set_ylabel("Area ($\mathrm{arcmin}^2$)")

    ax2.scatter(
        df_beams["date"], df_beams["nbeam"], color="black", marker=".", zorder=4
    )

    ax2.grid()
    ax2.set_ylabel("Nbeam")

    ax3.scatter(
        df_cbants["date"], df_cbants["nant_cb"], color="black", marker=".", zorder=4
    )

    ax3.grid()
    ax3.set_ylabel("$\mathrm{Nant}_\mathrm{cb}$")

    ax4.scatter(
        df_ibants["date"], df_ibants["nant_ib"], color="black", marker=".", zorder=4
    )

    ax4.grid()
    ax4.set_ylabel("$\mathrm{Nant}_\mathrm{ib}$")

    ax5.scatter(df["date"], df["tot_area"], color="black", marker=".", zorder=4)

    ax5.grid()
    ax5.set_ylabel("Tot_area ($\mathrm{deg}^2$)")
    ax5.set_xlabel("Date")

    fig.tight_layout()

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
    ax2.set_xlabel("Area (arcmin2)")

    fig.tight_layout()

    # total area histogram
    mask = df["tot_area"] > 0.05
    fig, (ax1, ax2) = plt.subplots(
        nrows=2, ncols=1, figsize=(6.4, 6.4), sharex=True, sharey=False
    )

    ax1.hist(
        df.loc[mask, "tot_area"],
        color="black",
        bins=71,
        density=True,
        histtype="step",
        lw=2,
        zorder=4,
    )

    ax1.axvline(
        x=np.median(df.loc[mask, "tot_area"]), color="gray", ls="dashed", lw=2, zorder=6
    )

    ax1.axvline(
        x=np.mean(df.loc[mask, "tot_area"]), color="C0", ls="dotted", lw=2, zorder=6
    )

    print(
        "Mean, median: {0:.2f} {1:.2f} deg2".format(
            np.nanmean(df.loc[mask, "tot_area"]), np.nanmedian(df.loc[mask, "tot_area"])
        )
    )

    ax1.grid()
    ax1.set_ylabel("PDF")

    ax2.hist(
        df.loc[mask, "tot_area"],
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

    fig.tight_layout()

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
