"""
marine_qc.py invoked by typing::

  python2.7 marine_qc.py -config configuration.txt -year1 1850 -year2 1855 -month1 1 -month2 1 [-tracking]

This quality controls data for the chosen years. The location of the data and the locations of the climatology files are
all to be specified in the configuration files.
"""

from __future__ import annotations

# external py modules
import argparse
import json
import logging
import os
import sys
from datetime import datetime

import pandas as pd

from glamod_marine_processing.qc_suite.modules import IMMA1
from glamod_marine_processing.qc_suite.modules import BackgroundField as bf
from glamod_marine_processing.qc_suite.modules import Climatology as clim
from glamod_marine_processing.qc_suite.modules import Extended_IMMA_sb as ex
from glamod_marine_processing.qc_suite.modules import noc_auxiliary, qc
from glamod_marine_processing.utilities import load_json


def read_icoads_file(
    year, month, icoads_dir, ids_to_exclude, tracking, parameters, climlib, config
):
    """Read ICOADS file."""
    logging.info(
        "INFO({}): {} {}".format(
            datetime.now().time().isoformat(timespec="milliseconds"), year, month
        )
    )

    last_year, last_month = qc.last_month_was(year, month)
    next_year, next_month = qc.next_month_is(year, month)

    reps = ex.Deck()
    count = 0
    lastday = -99

    for readyear, readmonth in qc.year_month_gen(
        last_year, last_month, next_year, next_month
    ):
        logging.info(
            "INFO({}): {} {}".format(
                datetime.now().time().isoformat(timespec="milliseconds"),
                readyear,
                readmonth,
            )
        )

        ostia_bg_var = None
        if tracking:
            ostia_bg_var = clim.Climatology.from_filename(
                config.get("Climatologies").get(
                    qc.season(readmonth) + "_ostia_background"
                ),
                "bg_var",
            )

        filename = icoads_dir + f"{readyear:4d}-{readmonth:02d}.psv"
        if not os.path.isfile(filename):
            logging.warning(f"File not available: {filename}.")
            continue
        imma_obj = pd.read_csv(
            filename,
            sep="|",
            header=None,
            names=[
                "YR",
                "MO",
                "DY",
                "HR",
                "LAT",
                "LON",
                "DS",
                "VS",
                "ID",
                "AT",
                "SST",
                "DPT",
                "DCK",
                "SLP",
                "SID",
                "PT",
                "UID",
                "W",
                "D",
                "IRF",
                "bad_data",
                "outfile",
            ],
            low_memory=False,
        )

        # replace ' ' in ID field with '' (corrections introduce bug)
        imma_obj["ID"].replace(" ", "", inplace=True)
        imma_obj = imma_obj.sort_values(
            ["YR", "MO", "DY", "HR", "ID"], axis=0, ascending=True
        )
        imma_obj = imma_obj.reset_index(drop=True)

        data_index = imma_obj.index

        rec = IMMA1.IMMA()
        logging.info(
            "INFO({}): Data read, applying first QC".format(
                datetime.now().time().isoformat(timespec="milliseconds")
            )
        )
        dyb_count = 0
        for idx in data_index:
            # set missing values to None
            for k, v in imma_obj.loc[idx,].to_dict().items():
                rec.data[k] = noc_auxiliary.to_none(v)
            readob = True
            if (
                rec.data["ID"] not in ids_to_exclude
                and readob
                and rec.data["YR"] == readyear
                and rec.data["MO"] == readmonth
                and rec.data["DY"] is not None
            ):
                rep = ex.MarineReportQC(rec)
                del rec

                rep.setvar("AT2", rep.getvar("AT"))

                # if day has changed then read in OSTIA field if available and append SST and sea-ice fraction
                # to the observation metadata
                if tracking and readyear >= 1985 and rep.getvar("DY") is not None:
                    if rep.getvar("DY") != lastday:
                        lastday = rep.getvar("DY")
                        y_year, y_month, y_day = qc.yesterday(
                            readyear, readmonth, lastday
                        )

                        #                            ofname = ostia_filename(ostia_dir, y_year, y_month, y_day)
                        ofname = bf.get_background_filename(
                            parameters["background_dir"],
                            parameters["background_filenames"],
                            y_year,
                            y_month,
                            y_day,
                        )

                        climlib.add_field(
                            "OSTIA",
                            "background",
                            clim.Climatology.from_filename(ofname, "analysed_sst"),
                        )
                        climlib.add_field(
                            "OSTIA",
                            "ice",
                            clim.Climatology.from_filename(ofname, "sea_ice_fraction"),
                        )

                    rep_clim = climlib.get_field("OSTIA", "background").get_value_ostia(
                        rep.lat(), rep.lon()
                    )
                    if rep_clim is not None:
                        rep_clim -= 273.15

                    rep.setext("OSTIA", rep_clim)
                    rep.setext(
                        "ICE",
                        climlib.get_field("OSTIA", "ice").get_value_ostia(
                            rep.lat(), rep.lon()
                        ),
                    )
                    rep.setext(
                        "BGVAR",
                        ostia_bg_var.get_value_mds_style(
                            rep.lat(), rep.lon(), rep.getvar("MO"), rep.getvar("DY")
                        ),
                    )

                for varname in ["SST", "AT"]:
                    rep_clim = climlib.get_field(varname, "mean").get_value_mds_style(
                        rep.lat(), rep.lon(), rep.getvar("MO"), rep.getvar("DY")
                    )
                    rep.add_climate_variable(varname, rep_clim)

                for varname in ["SLP2", "SHU", "CRH", "CWB", "DPD"]:
                    rep_clim = climlib.get_field(varname, "mean").get_value(
                        rep.lat(), rep.lon(), rep.getvar("MO"), rep.getvar("DY")
                    )
                    rep.add_climate_variable(varname, rep_clim)

                for varname in ["DPT", "AT2", "SLP"]:
                    rep_clim = climlib.get_field(varname, "mean").get_value(
                        rep.lat(), rep.lon(), rep.getvar("MO"), rep.getvar("DY")
                    )
                    rep_stdev = climlib.get_field(varname, "stdev").get_value(
                        rep.lat(), rep.lon(), rep.getvar("MO"), rep.getvar("DY")
                    )
                    rep.add_climate_variable(varname, rep_clim, rep_stdev)

                rep.calculate_humidity_variables(["SHU", "VAP", "CRH", "CWB", "DPD"])

                rep.perform_base_qc(parameters)
                rep.set_qc(
                    "POS",
                    "month_match",
                    qc.month_match(year, month, rep.getvar("YR"), rep.getvar("MO")),
                )

                reps.append(rep)
                count += 1

            rec = IMMA1.IMMA()
            dyb_count += 1
            if dyb_count % 1000 == 0:
                logging.info(
                    "INFO({}): {} out of {} processed".format(
                        datetime.now().time().isoformat(timespec="milliseconds"),
                        dyb_count,
                        imma_obj.index.size,
                    )
                )

            # icoads_file.close()
    return reps, count


def main(argv):
    """Main marine qc function.

    This program reads in data from ICOADS.3.0.0/ICOADS.3.0.1 and applies quality control processes to it, flagging data
    as good or bad according to a set of different criteria. Optionally it will replace drifting buoy SST data in
    ICOADS.3.0.1 with drifter data taken from the GDBC portal.

    The first step of the process is to read in various SST and MAT climatologies from file. These are 1degree latitude
    by 1 degree longitude by 73 pentad fields in NetCDF format.

    The program then loops over all specified years and months reads in the data needed to QC that month and then
    does the QC. There are three stages in the QC

    basic QC - this proceeds one observation at a time. Checks are relatively simple and detect gross errors

    track check - this works on Voyages consisting of all the observations from a single ship (or at least a single ID)
    and identifies observations which make for an implausible ship track

    buddy check - this works on Decks which are large collections of observations and compares observations to their
    neighbours
    """
    print("########################")
    print("Running make_and_full_qc")
    print("########################")

    parser = argparse.ArgumentParser(description="Marine QC system, main program")
    parser.add_argument(
        "-config", type=str, default="configuration.txt", help="name of config file"
    )
    parser.add_argument("-tracking", action="store_true", help="perform tracking QC")
    parser.add_argument("-jobs", type=str, default="jobs.json", help="name of job file")
    parser.add_argument("-job_index", type=int, default=0, help="job index")

    args = parser.parse_args()

    inputfile = args.config
    jobfile = args.jobs
    jobindex = args.job_index - 1
    tracking = args.tracking

    with open(jobfile) as fp:
        jobs = json.load(fp)

    year1 = jobs["jobs"][jobindex]["year1"]
    year2 = jobs["jobs"][jobindex]["year2"]
    month1 = jobs["jobs"][jobindex]["month1"]
    month2 = jobs["jobs"][jobindex]["month2"]

    verbose = True  # need set to read as arg in future

    logging.info("running on ICOADS, this is not a test!")

    logging.info(f"Input file is {inputfile}")
    logging.info(f"Running from {month1} {year1} to {month2} {year2}")
    logging.info("")

    config = load_json(inputfile)
    icoads_dir = config.get("Directories").get("ICOADS_dir")
    out_dir = config.get("Directories").get("out_dir")
    bad_id_file = config.get("Files").get("IDs_to_exclude")
    version = config.get("Icoads").get("icoads_version")

    logging.info(f"ICOADS directory = {icoads_dir}")
    logging.info(f"ICOADS version = {version}")
    logging.info(f"Output to {out_dir}")
    logging.info(f"List of bad IDs = {bad_id_file}")
    logging.info(
        "Parameter file = {}".format(config.get("Files").get("parameter_file"))
    )
    logging.info("")

    ids_to_exclude = bf.process_bad_id_file(bad_id_file)

    # read in climatology files
    sst_pentad_stdev = clim.Climatology.from_filename(
        config.get("Climatologies").get("Old_SST_stdev_climatology"), "sst"
    )

    sst_stdev_1 = clim.Climatology.from_filename(
        config.get("Climatologies").get("SST_buddy_one_box_to_buddy_avg"), "sst"
    )
    sst_stdev_2 = clim.Climatology.from_filename(
        config.get("Climatologies").get("SST_buddy_one_ob_to_box_avg"), "sst"
    )
    sst_stdev_3 = clim.Climatology.from_filename(
        config.get("Climatologies").get("SST_buddy_avg_sampling"), "sst"
    )

    with open(config.get("Files").get("parameter_file")) as f:
        parameters = json.load(f)

    logging.info("Reading climatologies from parameter file")
    climlib = ex.ClimatologyLibrary()
    for entry in parameters["climatologies"]:
        logging.info(f"{entry[0]} {entry[1]}")
        climlib.add_field(
            entry[0], entry[1], clim.Climatology.from_filename(entry[2], entry[3])
        )

    for year, month in qc.year_month_gen(year1, month1, year2, month2):
        reps, count = read_icoads_file(
            year,
            month,
            icoads_dir,
            ids_to_exclude,
            tracking,
            parameters,
            climlib,
            config,
        )

    logging.info(
        "INFO({}): Read {} ICOADS records".format(
            datetime.now().time().isoformat(timespec="milliseconds"), count
        )
    )

    # filter the obs into passes and fails of basic positional QC
    filt = ex.QC_filter()
    filt.add_qc_filter("POS", "date", 0)
    filt.add_qc_filter("POS", "time", 0)
    filt.add_qc_filter("POS", "pos", 0)
    filt.add_qc_filter("POS", "blklst", 0)

    reps.add_filter(filt)

    if verbose:
        logging.info(
            "INFO ({}) .... Track checking individual ships".format(
                datetime.now().time().isoformat(timespec="milliseconds")
            )
        )

        # track check the passes one ship at a time
    count_ships = 0
    for one_ship in reps.get_one_platform_at_a_time():
        one_ship.track_check(parameters["track_check"])
        one_ship.iquam_track_check(parameters["IQUAM_track_check"])
        one_ship.spike_check(parameters["IQUAM_spike_check"])
        one_ship.find_saturated_runs(parameters["saturated_runs"])
        one_ship.find_multiple_rounded_values(parameters["multiple_rounded_values"])

        for varname in ["SST", "AT", "AT2", "DPT", "SLP"]:
            one_ship.find_repeated_values(
                parameters["find_repeated_values"], intype=varname
            )

        count_ships += 1

    logging.info(f"Track checked {count_ships} ships")

    if verbose:
        logging.info(
            "INFO ({}) .... Applying buddy checks".format(
                datetime.now().time().isoformat(timespec="milliseconds")
            )
        )
    if verbose:
        logging.info(
            "INFO ({}) ........ SST".format(
                datetime.now().time().isoformat(timespec="milliseconds")
            )
        )
        # SST buddy check
    filt = ex.QC_filter()
    filt.add_qc_filter("POS", "is780", 0)
    filt.add_qc_filter("POS", "date", 0)
    filt.add_qc_filter("POS", "time", 0)
    filt.add_qc_filter("POS", "pos", 0)
    filt.add_qc_filter("POS", "blklst", 0)
    filt.add_qc_filter("POS", "trk", 0)
    filt.add_qc_filter("SST", "noval", 0)
    filt.add_qc_filter("SST", "freez", 0)
    filt.add_qc_filter("SST", "clim", 0)
    filt.add_qc_filter("SST", "nonorm", 0)

    reps.add_filter(filt)

    reps.bayesian_buddy_check("SST", sst_stdev_1, sst_stdev_2, sst_stdev_3, parameters)
    reps.mds_buddy_check("SST", sst_pentad_stdev, parameters["mds_buddy_check"])

    if verbose:
        logging.info(
            "INFO ({}) ........ NMAT".format(
                datetime.now().time().isoformat(timespec="milliseconds")
            )
        )
        # NMAT buddy check
    filt = ex.QC_filter()
    filt.add_qc_filter("POS", "isship", 1)  # only do ships mat_blacklist
    filt.add_qc_filter("AT", "mat_blacklist", 0)
    filt.add_qc_filter("POS", "date", 0)
    filt.add_qc_filter("POS", "time", 0)
    filt.add_qc_filter("POS", "pos", 0)
    filt.add_qc_filter("POS", "blklst", 0)
    filt.add_qc_filter("POS", "trk", 0)
    filt.add_qc_filter("POS", "day", 0)
    filt.add_qc_filter("AT", "noval", 0)
    filt.add_qc_filter("AT", "clim", 0)
    filt.add_qc_filter("AT", "nonorm", 0)

    reps.add_filter(filt)

    reps.bayesian_buddy_check("AT", sst_stdev_1, sst_stdev_2, sst_stdev_3, parameters)
    reps.mds_buddy_check("AT", sst_pentad_stdev, parameters["mds_buddy_check"])

    # DPT buddy check #NB no day check for this one
    filt = ex.QC_filter()
    filt.add_qc_filter("DPT", "hum_blacklist", 0)
    filt.add_qc_filter("POS", "date", 0)
    filt.add_qc_filter("POS", "time", 0)
    filt.add_qc_filter("POS", "pos", 0)
    filt.add_qc_filter("POS", "blklst", 0)
    filt.add_qc_filter("POS", "trk", 0)
    filt.add_qc_filter("DPT", "noval", 0)
    filt.add_qc_filter("DPT", "clim", 0)
    filt.add_qc_filter("DPT", "nonorm", 0)

    reps.add_filter(filt)

    reps.mds_buddy_check(
        "DPT", climlib.get_field("DPT", "stdev"), parameters["mds_buddy_check"]
    )

    if verbose:
        logging.info(
            "INFO ({}) ........ SLP".format(
                datetime.now().time().isoformat(timespec="milliseconds")
            )
        )
        # SLP buddy check
    filt = ex.QC_filter()
    filt.add_qc_filter("POS", "date", 0)
    filt.add_qc_filter("POS", "time", 0)
    filt.add_qc_filter("POS", "pos", 0)
    filt.add_qc_filter("POS", "blklst", 0)
    filt.add_qc_filter("POS", "trk", 0)
    filt.add_qc_filter("SLP", "noval", 0)
    filt.add_qc_filter("SLP", "clim", 0)
    filt.add_qc_filter("SLP", "nonorm", 0)

    reps.add_filter(filt)

    reps.mds_buddy_check(
        "SLP", climlib.get_field("SLP", "stdev"), parameters["slp_buddy_check"]
    )

    extdir = bf.safe_make_dir(out_dir, year, month)
    reps.write_output(parameters["runid"], extdir, year, month)

    if tracking:
        if verbose:
            logging.info(
                "INFO ({}) .... Tracking".format(
                    datetime.now().time().isoformat(timespec="milliseconds")
                )
            )

            # set QC for output by ID - buoys only and passes base SST QC
        filt = ex.QC_filter()
        filt.add_qc_filter("POS", "month_match", 1)
        filt.add_qc_filter("POS", "isdrifter", 1)

        reps.add_filter(filt)

        idfile = open(extdir + "/ID_file.txt", "w")
        for one_ship in reps.get_one_platform_at_a_time():
            if len(one_ship) > 0:
                thisid = one_ship.getrep(0).getvar("ID")
                if thisid is not None:
                    idfile.write(thisid + "," + ex.safe_filename(thisid) + "\n")
                    one_ship.write_output(parameters["runid"], extdir, year, month)
        idfile.close()

    del reps


if __name__ == "__main__":
    logging.basicConfig(
        format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
        level=logging.DEBUG,
        datefmt="%Y%m%d %H:%M:%S",
        filename=None,
    )

    main(sys.argv[1:])
