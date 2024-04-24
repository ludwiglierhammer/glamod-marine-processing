"""
Created on Wed Aug  3 09:37:04 2022

@author: sbiri
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

# %%
# def main(argv):
if 1:
    """
    simplified version of preprocess.py in qc_suite
    It reads in:
        valid data from level1d
        NOC_corrections duplicates
        level1a PT=7 data (in invalid or excluded directory)
    It exports a psv file
    """

    print("########################")
    print("Running preprocessing")
    print("########################")

    parser = argparse.ArgumentParser(
        description="Marine QC system, preprocessing program"
    )
    parser.add_argument(
        "-source", type=str, help="Path to level1d data files", required=True
    )
    parser.add_argument(
        "-dck_list", type=str, help="Path to source_deck_list.txt", required=True
    )
    parser.add_argument(
        "-dck_period", type=str, help="Path to source_deck_periods.json", required=True
    )
    parser.add_argument(
        "-corrections",
        type=str,
        help="Path to NOC correction data files",
        required=True,
    )
    parser.add_argument(
        "-destination", type=str, help="Path to output directory", required=True
    )
    parser.add_argument(
        "-release", type=str, help="Release identifier, e.g. release_5.1", required=True
    )
    parser.add_argument(
        "-update", type=str, help="Update identifyer, e.g. 000000", required=True
    )

    args = parser.parse_args()

    in_dir = args.source
    out_dir = args.destination
    corr = args.corrections
    dck_lst = args.dck_list
    dck_p = args.dck_period
    rel_id = args.release
    upd_id = args.update

    with open(dck_lst) as fO:
        dck_list = fO.read().splitlines()

    with open(dck_p) as fO:
        dck_period = json.load(fO)

    for dl in dck_list:
        y_init = np.minimum(dck_period[dl].get("year_init"), 2022)
        y_end = np.maximum(dck_period[dl].get("year_end"), 1948)

    # infile_patt = '-{}-{}.psv'.format(rel_id, upd_id)
    # verbose = True  # need set to read as arg in future

    for yr in range(y_init - 1, y_end + 2):
        # expanded to include dec of the privious year and jan of the following, for buddy checks (i think)
        if yr == y_init - 1:
            mos = [12]
        elif yr == y_end + 1:
            mos = [1]
        else:
            mos = range(1, 13)

        for mo in mos:
            print(yr, mo)
            # %% load duplicates flags
            dup_file = os.path.join(
                corr, "duplicate_flags", str(yr) + "-" + f"{mo:02d}" + ".txt.gz"
            )
            if not os.path.isfile(dup_file):
                print(
                    f"No NOC_correction duplicate file found for {yr}-{mo} at {dup_file}"
                )
                continue
            dup_flags = pd.read_csv(
                dup_file,
                delimiter="|",
                dtype="object",
                header=None,
                usecols=[0, 1, 2],
                names=["UID", "dup_flag", "dups"],
                quotechar=None,
                quoting=3,
            )
            dup_flags = dup_flags.set_index("UID")
            data = pd.DataFrame()
            # %%
            for dl in dck_list:
                print(dl)
                data_dl = pd.DataFrame()
                # read tables from level1d
                # from header get YR, MO, 'DY', 'HR', 'LAT', 'LON', 'ID',
                # 'DCK', 'SID', 'PT', 'UID', 'IRF', 'DS', 'VS'
                fn = os.path.join(
                    in_dir,
                    dl,
                    "header-" + str(yr) + "-" + f"{mo:02d}" + f"-{rel_id}-{upd_id}.psv",
                )
                if os.path.exists(fn):
                    print(f"Reading header {fn}")
                    rn = [
                        "report_id",
                        "region",
                        "sub_region",
                        "application_area",
                        "observing_programme",
                        "report_type",
                        "station_name",
                        "station_type",
                        "platform_type",
                        "platform_sub_type",
                        "primary_station_id",
                        "station_record_number",
                        "primary_station_id_scheme",
                        "longitude",
                        "latitude",
                        "location_accuracy",
                        "location_method",
                        "location_quality",
                        "crs",
                        "station_speed",
                        "station_course",
                        "station_heading",
                        "height_of_station_above_local_ground",
                        "height_of_station_above_sea_level",
                        "height_of_station_above_sea_level_accuracy",
                        "sea_level_datum",
                        "report_meaning_of_timestamp",
                        "report_timestamp",
                        "report_duration",
                        "report_time_accuracy",
                        "report_time_quality",
                        "report_time_reference",
                        "profile_id",
                        "events_at_station",
                        "report_quality",
                        "duplicate_status",
                        "duplicates",
                        "record_timestamp",
                        "history",
                        "processing_level",
                        "processing_codes",
                        "source_id",
                        "source_record_id",
                    ]
                    tmp = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=1,
                        names=rn,
                    )
                    # print("Reanaming")
                    tmp.rename(columns={"latitude": "LAT"}, inplace=True)
                    tmp.rename(columns={"longitude": "LON"}, inplace=True)
                    tmp.rename(columns={"primary_station_id": "ID"}, inplace=True)
                    tmp.rename(
                        columns={"platform_type": "PT"}, inplace=True
                    )  # this is transformed based on platform_type.json in code tables
                    tmp.rename(columns={"report_id": "UID"}, inplace=True)
                    tmp.rename(columns={"report_quality": "IRF"}, inplace=True)
                    tmp.rename(columns={"station_course": "DS"}, inplace=True)
                    tmp.rename(columns={"station_speed": "VS"}, inplace=True)
                    # print("splitting")
                    tmp["YR"] = tmp["report_timestamp"].apply(lambda x: x[0:4])
                    tmp["MO"] = tmp["report_timestamp"].apply(lambda x: x[5:7])
                    tmp["DY"] = tmp["report_timestamp"].apply(lambda x: x[8:10])
                    tmp["HR"] = tmp["report_timestamp"].apply(lambda x: x[11:13])
                    tmp["DCK"] = tmp["source_id"].apply(lambda x: x[18:21])
                    tmp["SID"] = tmp["source_id"].apply(lambda x: x[14:17])
                    data_dl = tmp[
                        [
                            "YR",
                            "MO",
                            "DY",
                            "HR",
                            "LAT",
                            "LON",
                            "ID",
                            "DCK",
                            "SID",
                            "PT",
                            "UID",
                            "IRF",
                            "DS",
                            "VS",
                        ]
                    ]
                    # reset IRF as in imma before cdm
                    loc0 = data_dl.IRF != 1
                    loc1 = data_dl.IRF == 1
                    data_dl.IRF.loc[loc0] = 1
                    data_dl.IRF.loc[loc1] = 0
                    data_dl = data_dl.set_index("UID")
                # %%from obsevations_at 'AT',
                fn = os.path.join(
                    in_dir,
                    dl,
                    "observations-at-"
                    + str(yr)
                    + "-"
                    + f"{mo:02d}"
                    + f"-{rel_id}-{upd_id}.psv",
                )
                if os.path.exists(fn):
                    print(f"Reading AT data {fn}")
                    rn = [
                        "observation_id",
                        "report_id",
                        "data_policy_licence",
                        "date_time",
                        "date_time_meaning",
                        "observation_duration",
                        "longitude",
                        "latitude",
                        "crs",
                        "z_coordinate",
                        "z_coordinate_type",
                        "observation_height_above_station_surface",
                        "observed_variable",
                        "secondary_variable",
                        "observation_value",
                        "value_significance",
                        "secondary_value",
                        "units",
                        "code_table",
                        "conversion_flag",
                        "location_method",
                        "location_precision",
                        "z_coordinate_method",
                        "bbox_min_longitude",
                        "bbox_max_longitude",
                        "bbox_min_latitude",
                        "bbox_max_latitude",
                        "spatial_representativeness",
                        "quality_flag",
                        "numerical_precision",
                        "sensor_id",
                        "sensor_automation_status",
                        "exposure_of_sensor",
                        "original_precision",
                        "original_units",
                        "original_code_table",
                        "original_value",
                        "conversion_method",
                        "processing_code",
                        "processing_level",
                        "adjustment_id",
                        "traceability",
                        "advanced_qc",
                        "advanced_uncertainty",
                        "advanced_homogenisation",
                        "source_id",
                    ]
                    tmp = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=1,
                        names=rn,
                    )
                    tmp.rename(columns={"report_id": "UID"}, inplace=True)
                    tmp.rename(columns={"observation_value": "AT"}, inplace=True)
                    tmp = tmp.astype({"AT": "float"})
                    tmp = tmp[["UID", "AT"]].set_index("UID")
                    tmp.AT = tmp.AT - 273.15  # reset to Celsius
                    data_dl = data_dl.merge(tmp, on="UID", how="left")
                # %% from obsevations_sst 'SST',
                fn = os.path.join(
                    in_dir,
                    dl,
                    "observations-sst-"
                    + str(yr)
                    + "-"
                    + f"{mo:02d}"
                    + f"-{rel_id}-{upd_id}.psv",
                )
                if os.path.exists(fn):
                    print("Reading sst data")
                    rn = [
                        "observation_id",
                        "report_id",
                        "data_policy_licence",
                        "date_time",
                        "date_time_meaning",
                        "observation_duration",
                        "longitude",
                        "latitude",
                        "crs",
                        "z_coordinate",
                        "z_coordinate_type",
                        "observation_height_above_station_surface",
                        "observed_variable",
                        "secondary_variable",
                        "observation_value",
                        "value_significance",
                        "secondary_value",
                        "units",
                        "code_table",
                        "conversion_flag",
                        "location_method",
                        "location_precision",
                        "z_coordinate_method",
                        "bbox_min_longitude",
                        "bbox_max_longitude",
                        "bbox_min_latitude",
                        "bbox_max_latitude",
                        "spatial_representativeness",
                        "quality_flag",
                        "numerical_precision",
                        "sensor_id",
                        "sensor_automation_status",
                        "exposure_of_sensor",
                        "original_precision",
                        "original_units",
                        "original_code_table",
                        "original_value",
                        "conversion_method",
                        "processing_code",
                        "processing_level",
                        "adjustment_id",
                        "traceability",
                        "advanced_qc",
                        "advanced_uncertainty",
                        "advanced_homogenisation",
                        "source_id",
                    ]
                    tmp = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=1,
                        names=rn,
                    )
                    tmp.rename(columns={"report_id": "UID"}, inplace=True)
                    tmp.rename(columns={"observation_value": "SST"}, inplace=True)
                    tmp = tmp[["UID", "SST"]].set_index("UID")
                    tmp = tmp.astype({"SST": "float"})
                    tmp.SST = tmp.SST - 273.15  # reset to Celsius
                    data_dl = data_dl.merge(tmp, on="UID", how="left")
                # %% from obsevations_dpt 'DPT',
                fn = os.path.join(
                    in_dir,
                    dl,
                    "observations-dpt-"
                    + str(yr)
                    + "-"
                    + f"{mo:02d}"
                    + f"-{rel_id}-{upd_id}.psv",
                )
                if os.path.exists(fn):
                    print("Reading dpt data")
                    rn = [
                        "observation_id",
                        "report_id",
                        "data_policy_licence",
                        "date_time",
                        "date_time_meaning",
                        "observation_duration",
                        "longitude",
                        "latitude",
                        "crs",
                        "z_coordinate",
                        "z_coordinate_type",
                        "observation_height_above_station_surface",
                        "observed_variable",
                        "secondary_variable",
                        "observation_value",
                        "value_significance",
                        "secondary_value",
                        "units",
                        "code_table",
                        "conversion_flag",
                        "location_method",
                        "location_precision",
                        "z_coordinate_method",
                        "bbox_min_longitude",
                        "bbox_max_longitude",
                        "bbox_min_latitude",
                        "bbox_max_latitude",
                        "spatial_representativeness",
                        "quality_flag",
                        "numerical_precision",
                        "sensor_id",
                        "sensor_automation_status",
                        "exposure_of_sensor",
                        "original_precision",
                        "original_units",
                        "original_code_table",
                        "original_value",
                        "conversion_method",
                        "processing_code",
                        "processing_level",
                        "adjustment_id",
                        "traceability",
                        "advanced_qc",
                        "advanced_uncertainty",
                        "advanced_homogenisation",
                        "source_id",
                    ]
                    tmp = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=1,
                        names=rn,
                    )
                    tmp.rename(columns={"report_id": "UID"}, inplace=True)
                    tmp.rename(columns={"observation_value": "DPT"}, inplace=True)
                    tmp = tmp[["UID", "DPT"]].set_index("UID")
                    tmp = tmp.astype({"DPT": "float"})
                    tmp.DPT = tmp.DPT - 273.15  # reset to Celsius
                    data_dl = data_dl.merge(tmp, on="UID", how="left")
                # %% from obsevations_slp 'SLP',
                fn = os.path.join(
                    in_dir,
                    dl,
                    "observations-slp-"
                    + str(yr)
                    + "-"
                    + f"{mo:02d}"
                    + f"-{rel_id}-{upd_id}.psv",
                )
                if os.path.exists(fn):
                    print("Reading slp data")
                    rn = [
                        "observation_id",
                        "report_id",
                        "data_policy_licence",
                        "date_time",
                        "date_time_meaning",
                        "observation_duration",
                        "longitude",
                        "latitude",
                        "crs",
                        "z_coordinate",
                        "z_coordinate_type",
                        "observation_height_above_station_surface",
                        "observed_variable",
                        "secondary_variable",
                        "observation_value",
                        "value_significance",
                        "secondary_value",
                        "units",
                        "code_table",
                        "conversion_flag",
                        "location_method",
                        "location_precision",
                        "z_coordinate_method",
                        "bbox_min_longitude",
                        "bbox_max_longitude",
                        "bbox_min_latitude",
                        "bbox_max_latitude",
                        "spatial_representativeness",
                        "quality_flag",
                        "numerical_precision",
                        "sensor_id",
                        "sensor_automation_status",
                        "exposure_of_sensor",
                        "original_precision",
                        "original_units",
                        "original_code_table",
                        "original_value",
                        "conversion_method",
                        "processing_code",
                        "processing_level",
                        "adjustment_id",
                        "traceability",
                        "advanced_qc",
                        "advanced_uncertainty",
                        "advanced_homogenisation",
                        "source_id",
                    ]
                    tmp = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=1,
                        names=rn,
                    )
                    tmp.rename(columns={"report_id": "UID"}, inplace=True)
                    tmp.rename(columns={"observation_value": "SLP"}, inplace=True)
                    tmp = tmp[["UID", "SLP"]].set_index("UID")
                    tmp = tmp.astype({"SLP": "float"})
                    tmp.SLP = tmp.SLP / 100  # reset to hPa
                    data_dl = data_dl.merge(tmp, on="UID", how="left")
                # %% from obsevations_ws 'W',
                fn = os.path.join(
                    in_dir,
                    dl,
                    "observations-ws-"
                    + str(yr)
                    + "-"
                    + f"{mo:02d}"
                    + f"-{rel_id}-{upd_id}.psv",
                )
                if os.path.exists(fn):
                    print("Reading W data")
                    rn = [
                        "observation_id",
                        "report_id",
                        "data_policy_licence",
                        "date_time",
                        "date_time_meaning",
                        "observation_duration",
                        "longitude",
                        "latitude",
                        "crs",
                        "z_coordinate",
                        "z_coordinate_type",
                        "observation_height_above_station_surface",
                        "observed_variable",
                        "secondary_variable",
                        "observation_value",
                        "value_significance",
                        "secondary_value",
                        "units",
                        "code_table",
                        "conversion_flag",
                        "location_method",
                        "location_precision",
                        "z_coordinate_method",
                        "bbox_min_longitude",
                        "bbox_max_longitude",
                        "bbox_min_latitude",
                        "bbox_max_latitude",
                        "spatial_representativeness",
                        "quality_flag",
                        "numerical_precision",
                        "sensor_id",
                        "sensor_automation_status",
                        "exposure_of_sensor",
                        "original_precision",
                        "original_units",
                        "original_code_table",
                        "original_value",
                        "conversion_method",
                        "processing_code",
                        "processing_level",
                        "adjustment_id",
                        "traceability",
                        "advanced_qc",
                        "advanced_uncertainty",
                        "advanced_homogenisation",
                        "source_id",
                    ]
                    tmp = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=1,
                        names=rn,
                    )
                    tmp.rename(columns={"report_id": "UID"}, inplace=True)
                    tmp.rename(columns={"observation_value": "W"}, inplace=True)
                    tmp = tmp[["UID", "W"]].set_index("UID")
                    data_dl = data_dl.merge(tmp, on="UID", how="left")
                # %% from obsevations_wd 'D',
                fn = os.path.join(
                    in_dir,
                    dl,
                    "observations-ws-"
                    + str(yr)
                    + "-"
                    + f"{mo:02d}"
                    + f"-{rel_id}-{upd_id}.psv",
                )
                if os.path.exists(fn):
                    print("Reading WD data")
                    rn = [
                        "observation_id",
                        "report_id",
                        "data_policy_licence",
                        "date_time",
                        "date_time_meaning",
                        "observation_duration",
                        "longitude",
                        "latitude",
                        "crs",
                        "z_coordinate",
                        "z_coordinate_type",
                        "observation_height_above_station_surface",
                        "observed_variable",
                        "secondary_variable",
                        "observation_value",
                        "value_significance",
                        "secondary_value",
                        "units",
                        "code_table",
                        "conversion_flag",
                        "location_method",
                        "location_precision",
                        "z_coordinate_method",
                        "bbox_min_longitude",
                        "bbox_max_longitude",
                        "bbox_min_latitude",
                        "bbox_max_latitude",
                        "spatial_representativeness",
                        "quality_flag",
                        "numerical_precision",
                        "sensor_id",
                        "sensor_automation_status",
                        "exposure_of_sensor",
                        "original_precision",
                        "original_units",
                        "original_code_table",
                        "original_value",
                        "conversion_method",
                        "processing_code",
                        "processing_level",
                        "adjustment_id",
                        "traceability",
                        "advanced_qc",
                        "advanced_uncertainty",
                        "advanced_homogenisation",
                        "source_id",
                    ]
                    tmp = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=1,
                        names=rn,
                    )
                    tmp.rename(columns={"report_id": "UID"}, inplace=True)
                    tmp.rename(columns={"observation_value": "D"}, inplace=True)
                    tmp = tmp[["UID", "D"]].set_index("UID")
                    data_dl = data_dl.merge(tmp, on="UID", how="left")
                # %% 'bad_data' set to False
                if not data_dl.empty:
                    data_dl.loc[:, "bad_data"] = False
                    # #%% 'outfile' set to MSNG
                    data_dl.loc[:, "outfile"] = None

                # %% load drifter data PT=7 from level1a excluded
                fn = os.path.join(
                    in_dir[:-8],
                    "level1a/excluded",
                    dl,
                    str(yr) + "-" + f"{mo:02d}" + f"-{rel_id}-{upd_id}-c1_PT.psv",
                )
                if os.path.exists(fn):
                    print("Looking for drifters")
                    rn = [
                        "YR",
                        "MO",
                        "DY",
                        "HR",
                        "LAT",
                        "LON",
                        "IM",
                        "ATTC",
                        "TI",
                        "LI",
                        "DS",
                        "VS",
                        "NID",
                        "II",
                        "ID",
                        "C1",
                        "DI",
                        "D",
                        "WI",
                        "W",
                        "VI",
                        "VV",
                        "WW",
                        "W1",
                        "SLP",
                        "A",
                        "PPP",
                        "IT",
                        "AT",
                        "WBTI",
                        "WBT",
                        "DPTI",
                        "DPT",
                        "SI",
                        "SST",
                        "N",
                        "NH",
                        "CL",
                        "HI",
                        "H",
                        "CM",
                        "CH",
                        "WD",
                        "WP",
                        "WH",
                        "SD",
                        "SP",
                        "SH",
                        "ATTI",
                        "ATTL",
                        "BSI",
                        "B10",
                        "B1",
                        "DCK",
                        "SID",
                        "PT",
                        "DUPS",
                        "DUPC",
                        "TC",
                        "PB",
                        "WX",
                        "SX",
                        "C2",
                        "SQZ",
                        "SQA",
                        "AQZ",
                        "AQA",
                        "UQZ",
                        "UQA",
                        "VQZ",
                        "VQA",
                        "PQZ",
                        "PQA",
                        "DQZ",
                        "DQA",
                        "ND",
                        "SF",
                        "AF",
                        "UF",
                        "VF",
                        "PF",
                        "RF",
                        "ZNC",
                        "WNC",
                        "BNC",
                        "XNC",
                        "YNC",
                        "PNC",
                        "ANC",
                        "GNC",
                        "DNC",
                        "SNC",
                        "CNC",
                        "ENC",
                        "FNC",
                        "TNC",
                        "QCE",
                        "LZ",
                        "QCZ",
                        "c1_ATTI",
                        "c1_ATTL",
                        "UID",
                        "RN1",
                        "RN2",
                        "RN3",
                        "RSA",
                        "IRF",
                    ]

                    selcols = [
                        "YR",
                        "MO",
                        "DY",
                        "HR",
                        "LAT",
                        "LON",
                        "ID",
                        "DCK",
                        "SID",
                        "PT",
                        "UID",
                        "IRF",
                        "DS",
                        "VS",
                        "AT",
                        "SST",
                        "DPT",
                        "SLP",
                        "W",
                        "D",
                    ]

                    drifters = pd.read_csv(
                        fn,
                        delimiter="|",
                        dtype="object",
                        header=None,
                        skiprows=2,
                        names=rn,
                        usecols=lambda c: c in set(selcols),
                    )

                    drifters = drifters[drifters["PT"] == "7"]

                    if not drifters.empty:
                        print("Adding drifters")
                        # drifters = tmp[['YR', 'MO', 'DY', 'HR', 'LAT', 'LON',
                        #                 'ID', 'DCK', 'SID', 'PT', 'UID', 'IRF',
                        #                 'DS', 'VS', 'AT', 'SST', 'DPT', 'SLP',
                        #                 'W', 'D']].copy()
                        drifters.loc[:, "bad_data"] = False
                        drifters.loc[:, "outfile"] = None
                        # here UID is source_uid; add prepend
                        prepend = "ICOADS-302-"
                        # drifters.loc[:,"UID"] = drifters["UID"].apply(lambda x: f"{prepend+x}")
                        drifters["UID"] = prepend + drifters.UID
                        drifters = drifters.set_index("UID")
                        # add to data dataframe
                        data_dl = data_dl.append(drifters)

                if data_dl.empty:
                    print("Dataframe is empty. Skipping")
                    continue

                # find duplicates in list
                # duplicates = [name for name in names if names.count(name) > 1]
                # unique_duplicates = list(set(duplicates))
                # print(unique_duplicates)
                # %% merge duplicate flags
                print("merging duplicate flags")
                data_dl = data_dl.merge(
                    dup_flags,
                    how="left",
                    left_index=True,
                    right_index=True,
                    suffixes=(False, False),
                )
                # Need to replace NaNs in dup_flag column with 4s
                data_dl[["dup_flag"]] = data_dl[["dup_flag"]].fillna("4")
                # print(data_dl['PT'] == '7')
                # For drifters we need to repalce dup with the IRF flag

                data_dl.loc[
                    (data_dl["PT"] == "7") & (data_dl["IRF"] == "1"), "dup_flag"
                ] = "0"  # unique
                data_dl.loc[
                    (data_dl["PT"] == "7") & (data_dl["IRF"] != "1"), "dup_flag"
                ] = "3"  # worst duplicate

                # convert to int
                data_dl = data_dl.astype({"dup_flag": "int32"})
                data_dl = data_dl.astype({"PT": "int32"})
                # exclude bad rows and rows we dont otherwise want to process
                # -----------------------------------------------------------
                # bad data_dl (that didn't validate against IMMA schema)
                bad_data = data_dl["bad_data"]

                # ship only
                ship = [np.nan, 0, 1, 2, 3, 4, 5, 7]
                ship_mask = data_dl["PT"].apply(lambda x: x in ship)

                # Duplicate  flags
                dups_to_use = [0, 1, 4]
                dup_field = "dup_flag"
                duplicate_mask = data_dl[dup_field].apply(lambda x: x in dups_to_use)

                # now apply masking to data frame
                data_dl = data_dl[((~bad_data) & ship_mask & duplicate_mask)]

                data = pd.concat([data, data_dl])
                print([(len(data_dl.index)), len(data.index)])

            # print(data.head())
            data.reset_index(inplace=True)
            print("Writing file")
            # print(data.head())
            data = data.sort_values(
                ["YR", "MO", "DY", "HR", "UID"], axis=0, ascending=True
            )
            data = data.reindex(
                columns=[
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
                ]
            )
            data.to_csv(
                out_dir + f"{yr:04d}-{mo:02d}.psv",
                sep="|",
                header=False,
                index=False,
                compression="infer",
            )

# if __name__ == '__main__':
#    main(sys.argv[1:])
