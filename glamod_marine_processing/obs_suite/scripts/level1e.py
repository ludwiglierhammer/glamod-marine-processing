"""
Created on Mon Jun 17 14:24:10 2019

See IMPORTANT NOTE!

Script to generate level1e CDM data: adding MO-QC (a.k.a. John's QC) flags

    - Reads QC files and creates unique flag per QC file (observed parameter)
      using columns from each QC file as parameterized at the very beginning.
      This is done with function get_qc_flags()
      See notes below on how QC files are expected to be

    - Creates the report_quality CDM field with function add_report_quality()
      See below notes on the rules to create it

    - Merge quality flags with CDM tables with function process_table()
      Here, additionally,  we set 'report_time_quality' to '2' to all reports

    - Log, per table, total number of records and qc flag counts

Note again that the following flagging is decided/set here, does not come from QC files:

    1) header.report_time_quality = '2', as by the time a report gets here we know
        that it is at least a valid datetime
    2) header.report_quality = following the rules in the notes below

Note also that if a report is not qced (not in QC files, like worst duplicates) we override the default
settings in the initial mappings (not all not-checked...) to not-checked with:

          -  observations*.quality_flag = '2'
          -  header.'report_time_quality' = '2'
          -  header.'report_quality' = '2'
          -  header.'location_quality' = '3'

The processing unit is the source-deck monthly set of CDM tables.

Outputs data to /<data_path>/<release>/<source>/level1e/<sid-dck>/table[i]-fileID.psv
Outputs quicklook info to:  /<data_path>/<release>/<source>/level1c/quicklooks/<sid-dck>/fileID.json

where fileID is yyyy-mm-release_tag-update_tag

Before processing starts:
    - checks the existence of all io subdirectories in level1d|e -> exits if fails
    - checks availability of the source header table -> exits if fails
    - checks existence of source observation tables -> exits if no obs tables -> requirement removed to
      give way to sid-dck monthly partitions with no obs tables
    - checks of existence of the monthly QC (POS) file -> exits if fails. See IMPORTANT NOTE!!!!
    - removes all level1e products on input file resulting from previous runs

Inargs:
-------
data_path: marine data path in file system
release: release tag
update: update tag
dataset: dataset tag
config_path: configuration file path
sid_dck: source-deck data partition (optional, from config_file otherwise)
year: data file year (yyyy) (optional, from config_file otherwise)
month: data file month (mm) (optional, from config_file otherwise)


On expected format and content of QC files:
-------------------------------------------

- qc monthly files in <data_path/<release>/<source>/metoffice_qc/base/<yyyy>/<mm>/<id>_qc_yyyymm_CCIrun.csv
  with id in [POS,SST,AT,SLP,DPT,W]
- qc monthly files assumed to have 1 hdr line (first) with column names
- qc monthly files with FS=','
- qc field names assumed as those listed in qc_columns below

Note that all the qc files have an entry per qced** report in its header table,
even if the corresponfing observed parameter does not have an entry in that report,
in which case has the 'noval' flag set to '1'

WE ASSUME HERE THAT ALL MEASURED PARAMETERS HAVE A NOVAL FLAG THAT WE USE TO
TELL APART MISSING AND FAILED

** per qced report, but duplicates are not qced....vaya caña!

Note also that since the qc files have a UID that is the imma UID, not the CDM
report_id, with the source prepended (ICOADS-30-UID for source ICOADS_R3.0.0),
and I still don't have the rules to build the CDM report_id from the source (any)
UID:

THE WAY QC-FILES UID AND CDM-TABLES REPORT_ID ARE LINKED HERE IS HARDCODED
IN FUNCTION get_qc_flags() TO RELEASE1 SOURCE ICOADS_R3.0.0T


report_quality flag rules:
--------------------------

+-----------------+--------------------+------------------------+
| POS             | PARAMS             | report_quality         |
+-----------------+--------------------+------------------------+
| passed          | all failed         | fail                   |
+-----------------+--------------------+------------------------+
|                 | rest               | pass                   |
+-----------------+--------------------+------------------------+
| failed          | all                | fail                   |
+-----------------+--------------------+------------------------+
| not checked     | at least 1 passed  | pass                   |
+-----------------+--------------------+------------------------+
| (3              | all failed         | fail                   |
+-----------------+--------------------+------------------------+
|                 | al not checked     | not checked            |
+-----------------+--------------------+------------------------+

Dev NOTES:
----------
There are some hardcoding for ICOADS_R3.0.0.T: we are looking for report_id in CDM
adding 'ICOADS_30' to the UID in the QC flags!!!!!

Maybe should pass a QC version configuration file, with the path
of the QC files relative to a set path (i.e. informing of the QC version)

.....

@author: iregon
"""

from __future__ import annotations

import copy
import datetime
import logging
import operator
import os
import sys
from importlib import reload

import numpy as np
import pandas as pd
from _utilities import (
    date_handler,
    paths_exist,
    read_cdm_tables,
    save_quicklook,
    script_setup,
    write_cdm_tables,
)
from cdm_reader_mapper.cdm_mapper.tables.tables import get_cdm_atts
from marine_qc import qc_grouped_reports, qc_individual_reports, qc_sequential_reports
from marine_qc.external_clim import Climatology
from marine_qc.multiple_row_checks import do_multiple_row_check

reload(logging)  # This is to override potential previous config of logging


# Functions--------------------------------------------------------------------
def get_single_qc_flag(df):
    """Get single QC flag from DataFrame containing multiple QC flags."""
    mask_0 = (df == 0).any(axis=1)
    mask_1 = (df == 1).any(axis=1)
    mask_2 = (df == 2).any(axis=1)
    mask_3 = (df == 3).any(axis=1)

    conditions = [mask_1, mask_0, mask_3, mask_2]
    choices = [1, 0, 3, 2]
    result = np.select(conditions, choices, default=2)
    return pd.Series(result, index=df.index, name="QC_FLAG")


def compare_quality_checks(df, location_quality, report_time_quality):
    """Compare entries with location_quality and report_time_quality."""
    df[location_quality == 2] = 1
    df[report_time_quality == 4] = 1
    df[report_time_quality == 5] = 1


def update_filenames(d):
    """Ad external file path to file names."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "file_name":
                d[k] = os.path.join(ext_path, v)
            elif isinstance(v, dict):
                update_filenames(v)


def open_netcdffiles(d):
    """Open filenames as Climatology objects."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "inputs":
                if not isinstance(v, dict):
                    continue
                d[k] = Climatology.open_netcdf_file(**v)
            elif isinstance(v, dict):
                open_netcdffiles(v)


def update_dtypes(data_df, table):
    """Update dtypes in DataFrame."""
    if table == "header":
        data_df["platform_type"] = data_df["platform_type"].astype(int)
        data_df["latitude"] = data_df["latitude"].astype(float)
        data_df["longitude"] = data_df["longitude"].astype(float)
        data_df["report_timestamp"] = pd.to_datetime(
            data_df["report_timestamp"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce",
        )
        data_df["station_speed"] = data_df["station_speed"].astype(float)
        data_df["station_course"] = data_df["station_course"].astype(float)
        data_df["report_quality"] = data_df["report_quality"].astype(int)
        data_df["location_quality"] = data_df["location_quality"].astype(int)
        data_df["report_time_quality"] = data_df["report_time_quality"].astype(int)
    else:
        data_df["observation_value"] = data_df["observation_value"].astype(float)
        data_df["latitude"] = data_df["latitude"].astype(float)
        data_df["longitude"] = data_df["longitude"].astype(float)
        data_df["date_time"] = pd.to_datetime(
            data_df["date_time"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce",
        )
        data_df["quality_flag"] = data_df["quality_flag"].astype(int)
    return data_df


def do_qc_individual(
    data_dict,
    report_quality,
    location_quality,
    report_time_quality,
    quality_flags,
):
    """Individual QC."""

    def do_qc_individual_header():
        # 1 Individual checks
        logging.info("1. Do individual checks")

        # 1.1. Header
        logging.info("1.1. Do header checks")
        qc_dict_header = qc_dict.get("header", {})

        data = data_dict["header"]

        # 1.1.1. Position check
        logging.info("1.1.1. Do positional checks")

        # Deselect already failed location_qualities
        data_pos = data[location_quality != 2]
        idx_pos = data_pos.index

        # Do position check
        qc_dict_pos = qc_dict_header.get("position_check", {})
        pos_qc = do_multiple_row_check(
            data=data_pos,
            qc_dict=qc_dict_pos,
            return_method=return_method,
        )
        pos_qc = get_single_qc_flag(pos_qc)
        pos_qc = pos_qc.replace({1: 2, 2: 3})
        location_quality.loc[idx_pos] = pos_qc

        # 1.1.2. Time check
        logging.info("1.1.2. Do time checks")

        # Deselect already failed report_time_qualities
        data_time = data[(report_time_quality != 4) & (report_time_quality != 5)]

        # Do time check
        qc_dict_tme = qc_dict_header.get("time_check", {})
        time_qc = do_multiple_row_check(
            data=data_time,
            qc_dict=qc_dict_tme,
            return_method=return_method,
        )
        time_qc = get_single_qc_flag(time_qc)
        time_qc = time_qc.replace({1: 5, 2: 4, 3: 4})
        invalid_indexes = time_qc[time_qc != 0].index
        report_time_quality.loc[invalid_indexes] = time_qc[invalid_indexes]

        # 1.1.3. Report quality
        logging.info("1.1.3. Set report quality")
        compare_quality_checks(report_quality, location_quality, report_time_quality)

    def do_qc_individual_observations():
        # 1.2. Observations
        logging.info("1.2. Do observations checks")

        # 1.2.1. Do observation check
        i = 1
        for obs_table in obs_tables:
            if obs_table not in data_dict.keys():
                continue
            logging.info(f"1.2.{i}. Do {obs_table} check")
            data = data_dict[obs_table]
            quality_flag = quality_flags[obs_table]

            # Deselect already failed quality_flags
            data = data.loc[quality_flag != 1]

            # Deselect already failed report_qualities
            data = data.loc[report_quality != 1]

            # Deselect missing values
            qc_dict_miss = qc_dict.get("observations", {}).get("missing_values")
            miss_qc = do_multiple_row_check(
                data=data,
                qc_dict=qc_dict_miss,
                return_method=return_method,
            )
            miss_qc = get_single_qc_flag(miss_qc)
            miss_indexes = miss_qc[miss_qc == 1].index
            quality_flag.loc[miss_indexes] = 3
            data = data.drop(index=miss_indexes)

            idx_qc = data.index

            preproc_dict = qc_dict.get("preprocessing", {}).get(obs_table, {})
            qc_dict_obs = qc_dict.get("observations", {}).get(obs_table, {})
            update_filenames(preproc_dict)
            open_netcdffiles(preproc_dict)
            obs_qc = do_multiple_row_check(
                data=data,
                preproc_dict=preproc_dict,
                qc_dict=qc_dict_obs,
                return_method=return_method,
            )
            obs_qc = get_single_qc_flag(obs_qc)

            # Flag quality_flag
            quality_flag.loc[idx_qc] = obs_qc
            compare_quality_checks(quality_flag, location_quality, report_time_quality)

            i += 1

    def do_qc_individual_combined():
        # 1.2.2. Do combined observation check
        qc_dict_comb = qc_dict.get("observations", {}).get("combined", {})
        i = 1
        for qc_name in qc_dict_comb.keys():
            logging.info(f"1.2.{i}. Do combined {qc_name} check")
            func = getattr(qc_individual_reports, qc_dict_comb[qc_name]["func"])
            tables = qc_dict_comb[qc_name]["tables"]
            names = qc_dict_comb[qc_name]["names"]
            inputs = {}
            calculate = True
            for ivar, table in tables.items():
                if table not in data_dict.keys():
                    calculate = False
                    break
                data = data_dict[table]
                column = names[ivar]
                inputs[ivar] = data[column]
            if calculate is False:
                continue
            series_list = list(inputs.values())
            common_indexes = set(series_list[0].index).intersection(
                *(s.index for s in series_list[1:])
            )
            common_indexes = list(common_indexes)
            for ivar, series in inputs.items():
                inputs[ivar] = inputs[ivar].loc[common_indexes]
            qc_flag = func(**inputs)
            idx_failed = qc_flag[qc_flag.isin([1])].index
            for table in tables.values():
                quality_flags[table].loc[idx_failed] = qc_flag.loc[idx_failed]

            i += 1

    # Get QC settings for individual reports
    qc_dict = params.qc_settings.get("individual_reports")

    # Do header QC
    do_qc_individual_header()

    # Do observations QC
    do_qc_individual_observations()

    # Do combined QC
    do_qc_individual_combined()

    # Return updated quality flags
    return report_quality, location_quality, report_time_quality, quality_flags


def do_qc_sequential(
    data_dict, report_quality, location_quality, quality_flags, idx_gnrc
):
    """Sequential QC."""

    def do_qc_sequential_header():
        # 2. Sequential checks
        logging.info("2. Do sequential checks")
        qc_dict = params.qc_settings.get("sequential_reports", {})

        # 2.1. Header
        logging.info("2.1. Do header checks")
        qc_dict_header = qc_dict.get("header", {})
        data = data_dict["header"].copy()

        # Deselect rows containing generic ids
        data = data.drop(index=idx_gnrc)

        i = 1
        for qc_name in qc_dict_header.keys():
            logging.info(f"2.1.{i}. Do {qc_name} check.")
            # Deselect already failed report_qualities
            data = data[~report_quality.loc[data.index].isin([1])]

            qc_dict_check = qc_dict_header[qc_name]
            func = getattr(qc_sequential_reports, qc_dict_check["func"])
            names = qc_dict_check.get("names", {})
            kwargs = qc_dict_check.get("arguments", {})
            idx_list = []
            for ps_id, subset in data.groupby("primary_station_id"):
                inputs = {k: subset[v] for k, v in names.items()}
                track_qc = func(**inputs, **kwargs)
                idx_failed = track_qc.index[track_qc == 1]
                if not idx_failed.empty:
                    idx_list.extend(idx_failed)

            location_quality.loc[idx_list] = 2
            report_quality.loc[idx_list] = 1

            i += 1

    def do_qc_sequential_observations():
        # 2.2. Observations
        logging.info("2.2. Do observation checks")

        # 2.2.1. Do observation track check
        qc_dict = params.qc_settings.get("sequential_reports", {}).get(
            "observations", {}
        )
        i = 1
        for obs_table in obs_tables:
            if obs_table not in data_dict.keys():
                continue

            logging.info(f"2.2.{i}. Do {obs_table} checks")
            quality_flag = quality_flags[obs_table]
            data = data_dict[obs_table]

            # Deselect rows containing generic ids
            idx_gnrc_obs = idx_gnrc.intersection(quality_flag.index)
            data = data.drop(index=idx_gnrc_obs)

            j = 1
            for qc_name in qc_dict.keys():
                logging.info(f"2.2.{i}.{j}. Do {qc_name} check")
                # Do the sequential check
                qc_dict_check = qc_dict[qc_name]
                func = getattr(qc_sequential_reports, qc_dict_check["func"])
                names = qc_dict_check.get("names", {})
                kwargs = qc_dict_check.get("arguments", {})
                preproc = qc_dict_check.get("preproc", {})
                tables = qc_dict_check.get("tables", None)
                if isinstance(tables, list) and obs_table not in tables:
                    continue

                # Deselect already failed quality flags
                data = data[~quality_flag.loc[data.index] == 1]

                # Optionally, preprocess data
                data_cp = data.copy()
                if obs_table in preproc.keys():
                    col = preproc[obs_table]["column"]
                    op_str = preproc[obs_table]["operation"]
                    op_symbol, operand = op_str.strip().split()
                    operand = float(operand)
                    data_cp[col] = op_map[op_symbol](data_cp[col], operand)

                idx_list = []
                for ps_id, subset in data_dict["header"].groupby("primary_station_id"):
                    indexes = data_cp.index.intersection(subset.index)
                    subset_obs = data_cp.loc[indexes]
                    if subset_obs.empty:
                        continue
                    inputs = {k: subset_obs[v] for k, v in names.items()}
                    track_qc = func(**inputs, **kwargs)
                    idx_failed = track_qc.index[track_qc == 1]
                    if not idx_failed.empty:
                        idx_list.extend(idx_failed)

                quality_flag.loc[idx_list] = 1

                j += 1

            i += 1

    def do_qc_sequential_combined():
        # 2.2.2. Do combined observations track check
        qc_dict = params.qc_settings.get("sequential_reports", {}).get("combined", {})
        # !!!! Need updates
        return

        i = 1
        for qc_name in qc_dict.keys():
            logging.info(f"2.2.{i}. Do {qc_name} check")
            func = getattr(qc_sequential_reports, qc_dict[qc_name]["func"])
            tables = qc_dict[qc_name]["tables"]
            names = qc_dict[qc_name]["names"]
            kwargs = qc_dict[qc_name]["arguments"]

            inputs = {}
            for ivar, table in tables.items():
                data = data_dict[table]
                column = names[ivar]
                inputs[ivar] = data[column]
            series_list = list(inputs.values())
            common_indexes = set(series_list[0].index).intersection(
                *(s.index for s in series_list[1:])
            )
            common_indexes = list(common_indexes)
            for ivar, series in inputs.items():
                inputs[ivar] = inputs[ivar].loc[common_indexes]
            qc_flag = func(**inputs, **kwargs)
            idx_failed = qc_flag[qc_flag.isin([1])].index
            for table in tables.values():
                quality_flags[table].loc[idx_failed] = qc_flag.loc[idx_failed]
            i += 1

    do_qc_sequential_header()

    do_qc_sequential_observations()

    do_qc_sequential_combined()

    return report_quality, location_quality, quality_flags


def do_qc_grouped(data_dict, quality_flags):
    """Grouped QC."""
    # 3. Buddy check
    logging.info("3. Do buddy checks")
    qc_dict = params.qc_settings.get("grouped_reports")

    # 3.1. Do observation buddy check
    preproc_dict = qc_dict.get("preprocessing", {})
    qc_dict_obs = qc_dict.get("observations")

    qc_dict_ind = params.qc_settings.get("individual_reports")
    preproc_dict_ind = qc_dict_ind.get("preprocessing", {})

    # Copy params for C-RAID
    params_craid = copy.deepcopy(params)
    params_craid.prev_level_path = params.prev_level_path.replace(
        params.dataset, "C-RAID_1.2"
    )
    params_craid.prev_level_path = params_craid.prev_level_path.replace(
        params.sid_dck, "202412"
    )

    i = 1
    for obs_table in obs_tables:
        if obs_table not in data_dict.keys():
            continue
        logging.info(f"3.{i}. Do {obs_table} checks")
        quality_flag = quality_flags[obs_table]
        data = data_dict[obs_table]

        # Add C-RAID data
        db_craid = read_cdm_tables(params_craid, obs_table)
        if not db_craid.empty:
            data_craid = db_craid[obs_table].set_index("report_id", drop=False)
            update_dtypes(data_craid, obs_table)
            data_obs = pd.concat([data, data_craid])
            indexes_craid = data_craid.index
            ignore_indexes = data_obs.index.get_indexer(indexes_craid)
        else:
            logging.warning(
                f"Could not find any {obs_table} C-RAID_1.2 data for {params_craid.prev_fileID}: {params_craid.prev_level_path}"
            )
            indexes_craid = []
            ignore_indexes = None

        # Pre-processing
        preproc_dict_obs = preproc_dict.get(obs_table, {})
        preproc_dict_ind_obs = preproc_dict_ind.get(obs_table, {})

        for var_name in preproc_dict_obs.keys():
            if preproc_dict_obs[var_name] == "__individual_reports__":
                preproc_dict_obs[var_name] = preproc_dict_ind_obs.get(var_name, {}).get(
                    "inputs"
                )

        update_filenames(preproc_dict_obs)
        open_netcdffiles(preproc_dict_obs)

        # Get table-specific arguments
        qc_dict_obs_sp = qc_dict.get(obs_table, {})

        for var_name in preproc_dict_obs.keys():
            if not isinstance(preproc_dict_obs[var_name], dict):
                continue
            if "inputs" in preproc_dict_obs[var_name].keys():
                preproc_dict_obs[var_name] = preproc_dict_obs[var_name]["inputs"]

        j = 1
        for qc_name in qc_dict_obs.keys():
            if obs_table not in qc_dict_obs[qc_name]["tables"]:
                continue
            logging.info(f"3.{i}.{j}. Do {qc_name} check")

            # Deselect already failed quality flags
            obs_indexes = data.index.difference(indexes_craid)
            failed_indexes = quality_flag.loc[obs_indexes].isin([1]).index
            data = data.drop(failed_indexes)

            # Do the buddy check
            qc_dict_check = qc_dict_obs[qc_name]
            func = getattr(qc_grouped_reports, qc_dict_check["func"])
            names = qc_dict_check.get("names", {})
            inputs = {k: data[v] for k, v in names.items()}
            kwargs = qc_dict_check.get("arguments", {})
            for var_name, value in kwargs.items():
                if isinstance(value, str) and value == "__preprocessed__":
                    kwargs[var_name] = preproc_dict_obs[var_name]
            kwargs["ignore_indexes"] = ignore_indexes
            for arg_name, arg_value in qc_dict_obs_sp.get(qc_name, {}).items():
                kwargs[arg_name] = arg_value

            qc_flag = func(**inputs, **kwargs)
            idx_failed = qc_flag[qc_flag.isin([1])].index
            quality_flag.loc[idx_failed] = qc_flag.loc[idx_failed]

            j += 1

        i += 1

    return quality_flags


def do_qc(
    data_dict, report_quality, location_quality, report_time_quality, quality_flags
):
    """QC."""
    # Set observation quality_flag on blacklist and deselect them
    data_dict_orig = {}
    idx_blck = report_quality[report_quality == 6].index
    for table in data_dict.keys():
        data_dict_orig[table] = data_dict[table].copy()
        if table == "header":
            data_dict[table].drop(index=idx_blck, inplace=True)
            continue

        idx_blck_obs = idx_blck.intersection(quality_flags[table].index)
        quality_flags[table].loc[idx_blck_obs] = 6
        data_dict[table].drop(index=idx_blck_obs, inplace=True)

    # Set indexes of generic ID reports
    idx_gnrc = report_quality[report_quality == 88].index

    # Do the quality control
    report_quality, location_quality, report_time_quality, quality_flags = (
        do_qc_individual(
            data_dict=data_dict,
            report_quality=report_quality,
            location_quality=location_quality,
            report_time_quality=report_time_quality,
            quality_flags=quality_flags,
        )
    )

    report_quality, location_quality, quality_flags = do_qc_sequential(
        data_dict=data_dict,
        report_quality=report_quality,
        location_quality=location_quality,
        quality_flags=quality_flags,
        idx_gnrc=idx_gnrc,
    )

    quality_flags = do_qc_grouped(
        data_dict=data_dict,
        quality_flags=quality_flags,
    )

    # Update data dict
    history_add = f";{history_tstmp}. {params.history_explain}"
    header_df = data_dict_orig["header"]
    header_df["location_quality"] = location_quality
    header_df["report_time_quality"] = report_time_quality
    header_df["report_quality"] = report_quality

    header_df.update(
        header_df.loc[~header_df.index.isin(idx_blck), "history"].apply(
            lambda x: x + history_add
        )
    )

    for obs_table in obs_tables:
        if obs_table not in data_dict_orig.keys():
            continue
        obs_df = data_dict_orig[obs_table]
        obs_df["quality_flag"] = quality_flags[obs_table]

    return data_dict_orig


op_map = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
}

# Some other parameters -------------------------------------------------------
cdm_atts = get_cdm_atts()
obs_tables = [x for x in cdm_atts.keys() if x != "header"]

try:
    history_tstmp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
except AttributeError:  # for python < 3.11
    history_tstmp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# -----------------------------------------------------------------------------

# MAIN ------------------------------------------------------------------------

# Process input, set up some things and make sure we can do something   -------
logging.basicConfig(
    format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
    level=logging.INFO,
    datefmt="%Y%m%d %H:%M:%S",
    filename=None,
)

process_options = [
    "qc_settings",
    "history_explain",
    "no_qc_suite",
]
params = script_setup(process_options, sys.argv)
return_method = "failed"

# DO SOME PREPROCESSING ------------------------------------------------------

# Set file path to external files
ext_path = os.path.join(params.data_path, "external_files")
paths_exist(ext_path)

# Do some additional checks before clicking go, do we have a valid header?
header_filename = params.filename
if not os.path.isfile(header_filename):
    logging.error(f"Header table file not found: {header_filename}")
    sys.exit(1)

header_db = read_cdm_tables(params, "header")

if header_db.empty:
    logging.error("Empty or non-existing header table")
    sys.exit(1)

data_dict = {}
data_dict["header"] = header_db["header"]

# See what CDM tables are available for this fileID
tables_in = ["header"]
for table in obs_tables:
    table_filename = header_filename.replace("header", table)
    if not os.path.isfile(table_filename):
        logging.warning(f"CDM table not available: {table_filename}")
        continue
    tables_in.append(table)

if len(tables_in) == 1:
    logging.error(
        f"NO OBS TABLES AVAILABLE: {params.sid_dck}, period {params.year}-{params.month}"
    )
    sys.exit()

# Remove report_ids without any observations
report_ids = pd.Series()
for table_in in tables_in:
    if table_in not in data_dict.keys():
        db_ = read_cdm_tables(params, table_in)
        if db_.empty:
            continue
        data_dict[table_in] = db_[table_in]
    report_ids = pd.concat(
        [report_ids, data_dict[table_in]["report_id"]], ignore_index=True
    )

report_ids = report_ids[report_ids.duplicated()]

ql_dict = {}
quality_flags = {}
report_quality = pd.Series()
location_quality = pd.Series()
report_time_quality = pd.Series()

for table, df in data_dict.items():
    df = df.set_index("report_id", drop=False)
    p_length = len(df)
    valid_indexes = df.index.intersection(report_ids)
    df = df.loc[valid_indexes]
    update_dtypes(df, table)

    data_dict[table] = df

    if table == "header":
        report_quality = df["report_quality"].copy()
        location_quality = df["location_quality"].copy()
        report_time_quality = df["report_time_quality"].copy()
    else:
        quality_flags[table] = df["quality_flag"].copy()

    c_length = len(df)
    r_length = p_length - c_length
    ql_dict[table] = {
        "total": c_length,
        "deleted": r_length,
    }

# DO THE DATA PROCESSING ------------------------------------------------------
if params.no_qc_suite is not True:
    data_dict = do_qc(
        data_dict=data_dict,
        report_quality=report_quality,
        location_quality=location_quality,
        report_time_quality=report_time_quality,
        quality_flags=quality_flags,
    )


# WRITE QC FLAGS TO DATA ------------------------------------------------------
ql_dict["header"]["location_quality_flag"] = (
    data_dict["header"]["location_quality"].value_counts(dropna=False).to_dict()
)
ql_dict["header"]["report_quality_flag"] = (
    data_dict["header"]["report_quality"].value_counts(dropna=False).to_dict()
)
ql_dict["header"]["report_time_quality_flag"] = (
    data_dict["header"]["report_time_quality"].value_counts(dropna=False).to_dict()
)

for table, df in data_dict.items():
    write_cdm_tables(params, df, tables=table)

# CHECKOUT --------------------------------------------------------------------
logging.info("Saving json quicklook")
save_quicklook(params, ql_dict, date_handler)
