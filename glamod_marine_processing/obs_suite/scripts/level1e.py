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

import datetime
import logging
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

from glamod_marine_processing.qc_suite.modules.multiple_row_checks import (
    do_multiple_row_check,
)
from glamod_marine_processing.qc_suite.modules.next_elvel_deck_qc import (
    do_bayesian_buddy_check,
    do_mds_buddy_check,
)
from glamod_marine_processing.qc_suite.modules.next_level_track_check_qc import (
    do_few_check,
    do_iquam_track_check,
    do_spike_check,
    do_track_check,
    find_multiple_rounded_values,
    find_repeated_values,
    find_saturated_runs,
)

reload(logging)  # This is to override potential previous config of logging


# Functions--------------------------------------------------------------------
def get_single_qc_flag(df):
    return df


def compare_quality_checks(df):
    """Compare entries with location_quality and report_time_quality."""
    df = df.mask(location_quality == "2", "1")
    df = df.mask(report_time_quality == "4", "1")
    df = df.mask(report_time_quality == "5", "1")
    return df


# This is to apply the qc flags and write out flagged tables
def process_table(table_df, table, pass_time=None):
    """Process table."""
    if pass_time is None:
        pass_time = "2"
    not_checked_report = "2"
    not_checked_location = "3"
    not_checked_param = "2"
    logging.info(f"Processing table {table}")

    if isinstance(table_df, str):
        # Assume 'header' and in a DF in table_df otherwise
        # Open table and reindex
        table_df = read_cdm_tables(params, table)

        if table_df is None or table_df.empty:
            logging.warning(f"Empty or non existing table {table}")
            return
        table_df = table_df[table].set_index("report_id", drop=False)

    previous = len(table_df)
    table_df = table_df[table_df["report_id"].isin(report_ids)]
    total = len(table_df)
    removed = previous - total
    ql_dict[table] = {
        "total": total,
        "deleted": removed,
    }
    if table_df.empty:
        logging.warning(f"Empty table {table}.")
        return

    if flag:
        qc = table_qc.get(table).get("qc")
        element = table_qc.get(table).get("element")
        qc_table = qc_df[[qc]]
        qc_table = qc_table.rename({qc: element}, axis=1)
        table_df.update(qc_table)

        updated_locs = qc_table.loc[qc_table.notna().all(axis=1)].index

        if table != "header":
            ql_dict[table]["quality_flag"] = (
                table_df[element].value_counts(dropna=False).to_dict()
            )

        if table == "header":
            table_df.update(qc_df["report_quality"])
            history_add = f";{history_tstmp}. {params.history_explain}"
            table_df.loc[:, "report_time_quality"] = pass_time
            ql_dict[table]["location_quality_flag"] = (
                table_df["location_quality"].value_counts(dropna=False).to_dict()
            )
            ql_dict[table]["report_quality_flag"] = (
                table_df["report_quality"].value_counts(dropna=False).to_dict()
            )
            table_df.update(
                table_df.loc[updated_locs, "history"].apply(lambda x: x + history_add)
            )
    # Here very last minute change to account for reports not in QC files:
    # need to make sure it is all not-checked!
    # Test new things with 090-221. See 1984-03.
    # What happens if not POS flags matching?
    else:
        if table != "header":
            table_df.loc[:, "quality_flag"] = not_checked_param
        else:
            table_df.loc[:, "report_time_quality"] = pass_time
            table_df.loc[:, "report_quality"] = not_checked_report
            table_df.loc[:, "location_quality"] = not_checked_location

    if table != "header":
        table_df.loc[:, "quality_flag"] = compare_quality_checks(
            table_df["quality_flag"]
        )
    if table == "header":
        table_df.loc[:, "report_quality"] = compare_quality_checks(
            table_df["report_quality"]
        )

    write_cdm_tables(params, table_df, tables=table)


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

# Check we have all the dirs!
paths_exist(qc_path)

# Do some additional checks before clicking go, do we have a valid header?
header_filename = params.filename
if not os.path.isfile(header_filename):
    logging.error(f"Header table file not found: {header_filename}")
    sys.exit(1)

data_dict = {}

data_dict["header"] = read_cdm_tables(params, "header")

if header_df.empty:
    logging.error("Empty or non-existing header table")
    sys.exit(1)

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

for table, df in data_dict.items():
    df = df.set_index("report_id", drop=False)
    data_dict[table] = df.loc[report_ids]

# DO THE DATA PROCESSING ------------------------------------------------------

# 1. Observational checks
# 1.1. Header
header_df = data_dict["header"].copy()
idx_blck = header_df[header_df["report_quality"] == "6"].index
idx_gnrc = header_df[header_df["report_quality"] == "88"].index

# Deselect rows on blacklist
data = header_df.drop(index=idx_blck)

# Select header quality flags
report_quality = data["report_quality"].copy()
location_quality = data["location_quality"].copy()
report_time_quality = data["report_time_quality"].copy()

# 1.1.1. Position check
# Deselect already failed location_qualities
data_pos = data[~location_quality.isin(["2"])]
idx_pos = data_pos.idx

# Do position check
qc_dict = params.qc_settings.get("position_check", {}).get("header", {})
pos_qc = do_multiple_row_check(
    data=data_pos,
    qc_dict=qc_dict,
    return_method=return_method,
)
pos_qc = get_single_qc_flag(pos_qc)
location_quality.loc[idx_pos] = pos_qc

# 1.1.2. Time check
# Deselect already failed report_time_qualities
data_time = data[~report_time_quality.isin(["4", "5"])]
idx_time = data_time.idx

# Do time check
qc_dict = params.qc_settings.get("time_check", {}).get("header", {})
time_qc = do_multiple_row_check(
    data=data_time,
    qc_dict=qc_dict,
    return_method=return_method,
)
time_qc = get_single_qc_flag(time_qc)
report_time_quality.loc[idx_time] = time_qc

# 1.1.3. Report quality
report_quality = compare_quality_checks(report_time_quality)

# 1.2. Observations
quality_flags = {}
for obs_table in obs_tables:
    data = data_dict[obs_table].copy()
    # Select observation quality_flag
    quality_flag = data["quality_flag"]
    quality_flag.loc[idx_blck] = "6"

    # Deselect rows on blacklist
    data = data.drop(index=idx_blck)

    # Deselect already failed quality_flags
    data_qc = data[~quality_flag.isin("1")]
    # Deselect already failed report_qualities
    data_qc = data_qc[~report_quality.isin("1")]
    idx_qc = data_qc.index

    # Do observation check
    preproc_dict = params.qc_settings.get("preprocessing", {}).get(obs_table, {})
    qc_dict = params.qc_settings.get("observations_check", {}).get(obs_table, {})
    obs_qc = do_multiple_row_check(
        data=data_qc,
        preproc_dict=preproc_dict,
        qc_dict=qc_dict,
        return_method=return_method,
    )
    obs_qc = get_single_qc_flag(obs_qc)

    # Flag quality_flag
    quality_flag.loc[idx_qc] = obs_qc
    quality_flags[obs_table] = compare_quality_checks(quality_flag)

# 2. Track check
# 2.1. Header
# Deselect rows on blacklist
data = header_df.drop(index=idx_blck)
# Deselect rows containing generic ids
data = data.drop(index=gnrc_idx)
# Deselect already failed report_qualities
data = data[~report_quality.isin(["1"])]

qc_dict = params.qc_settings.get("track_check", {}).get("header", {})
for qc_name in qc_dict.keys():
    func = globals().get(qc_dict[qc_name]["func"])
    names = qc_dict[qc_name].get("names", {})
    inputs = {k: data[v] for k, v in names}
    kwargs = qc_dict[qc_name].get("arguments", {})
    track_qc = func(**inputs, **kwargs)
    idx_failed = track_qc[track_qc.isin("1")].index
    report_quality.loc[idx_failed] = track_qc.loc[idx_failed]

# ?. PROCESS QC FLAGS ---------------------------------------------------------
# Replace QC flags in C-RAID data; other approach needed!!!
# pass_time = None
# if params.no_qc_suite:
#    qc_avail = True
#    # Set report_quality to passed if report_quality is not checked
#    qc_df["report_quality"] = header_db["report_quality"]
#    qc_df["report_quality"] = qc_df["report_quality"].mask(
#        qc_df["report_quality"] == "2", "0"
#    )
#    pass_time = header_db["report_time_quality"]
#
# qc_df = qc_df[qc_df.index.isin(report_ids)]

# CHECKOUT --------------------------------------------------------------------
logging.info("Saving json quicklook")
save_quicklook(params, ql_dict, date_handler)
