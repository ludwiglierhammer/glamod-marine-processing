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

import pandas as pd
from _utilities import level3_columns, paths_exist, script_setup
from cdm_reader_mapper import cdm_mapper as cdm

reload(logging)  # This is to override potential previous config of logging


# FUNCTIONS -------------------------------------------------------------------
def copyfiles(pattern, dest, mode="excluded"):
    """Copy file pattern to dest."""
    file_list = glob.glob(pattern)
    for file_ in file_list:
        file_name = Path(file_).name
        shutil.copyfile(file_, os.path.join(dest, file_name))
        logging.info(f"{file_name} {mode} from level2 in {dest}")


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

# These to build the brace expansions for the out of release periods
left_min_period = 1600
right_max_period = 2100

paths_exist([params.level_excluded_path, params.level_reports_path])

# DO THE DATA SELECTION -------------------------------------------------------
# -----------------------------------------------------------------------------
obs_table = "observations-slp"
header_table = "header"
cdm_tables = [header_table, obs_table]

history_tstmp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

table_df = cdm.read_tables(
    params.prev_level_path, params.prev_fileID, cdm_subset=cdm_tables, na_values="null"
)

cdm_obs_core_df = pd.DataFrame(columns=level3_columns.keys())
