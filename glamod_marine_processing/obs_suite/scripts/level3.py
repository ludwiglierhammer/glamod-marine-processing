"""
Script to convert C3S CDM Marine level2 data into CDM OBS CORE pressure only data.

The processing unit is the source-deck.

Outputs included data to /<data_path>/<release>/<source>/level3/<sid-dck>/table[i]-fileID.psv

where fileID is yyyy-mm-release_tag-update_tag

Before processing starts:
    - checks the existence of input data subdirectory in level2 -> exits if fails
    - checks the existence of the level3 selection file (level3_list) and that
      sid-dck is registered in it -> exits if fails
    - checks that a sid-dck to be included has at least an observation table
      registered to be included  -> exits if fails

If at any point during copying an exception is raised, cleans sid-dck level3
before exiting.

Inargs:
-------
data_path: data release parent path (i.e./gws/nopw/c3s311_lot2/data/marine)
sid_dck: source-deck partition (sss-ddd)
release: release identifier
update: release update identifier
source: source dataset identifier
"""

from __future__ import annotations

import datetime
import glob
import logging
import os
import shutil
import sys
from importlib import reload
from pathlib import Path

from _utilities import FFS, level3_columns, script_setup, table_to_csv
from cdm_reader_mapper import cdm_mapper as cdm

reload(logging)  # This is to override potential previous config of logging


# FUNCTIONS -------------------------------------------------------------------
def process_table(table_df):
    """Process table."""
    cdm_obs_core_df = table_df[level3_columns]
    new_cols = [col[1] for col in cdm_obs_core_df.columns]
    cdm_obs_core_df.columns = new_cols

    cdm_obs_core_df = cdm_obs_core_df[cdm_obs_core_df["observation_value"].notnull()]

    odata_filename = os.path.join(
        params.level_path, FFS.join([params.fileID, "pressure_data"]) + ".psv"
    )
    table_to_csv(cdm_obs_core_df, odata_filename)
    logging.info(f"File written: {odata_filename}")


# MAIN ------------------------------------------------------------------------

# Process input and set up some things and make sure we can do something-------
logging.basicConfig(
    format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
    level=logging.INFO,
    datefmt="%Y%m%d %H:%M:%S",
    filename=None,
)
args = []
if len(sys.argv) > 1:
    logging.info("Reading command line arguments")
    args = sys.argv
else:
    logging.error("Need arguments to run!")

params = script_setup([], args)

# DO THE DATA SELECTION -------------------------------------------------------
# -----------------------------------------------------------------------------
obs_table = "observations-slp"
header_table = "header"
cdm_tables = [header_table, obs_table]

history_tstmp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

table_df = cdm.read_tables(
    params.prev_level_path, params.prev_fileID, cdm_subset=cdm_tables, na_values="null"
)

if not table_df.empty:
    process_table(table_df)
else:
    logging.warning(f"No CDM tables available for: {params.prev_fileID}.")
