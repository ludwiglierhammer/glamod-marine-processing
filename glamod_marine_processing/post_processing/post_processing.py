"""Split original ICOADS data into monthly source and deck files."""

from __future__ import annotations

import csv
import glob
import json
import os
from pathlib import Path
import pandas as pd
from cdm_reader_mapper import cdm_mapper

# default input file source pattern
_dataset = "C-RAID_1.2"
_release = "release_7.0"
_update = "000000"

def get_outfile_name(basepath, tag, dataset, year, month):
    """Generate output file name."""
    filename = f"{dataset}_{tag}_{year:04d}-{month:02d}"
    return f"{basepath}/{tag}/{os.path.basename(filename)}"

def get_year_month(df, time_axis):
    dates = df[time_axis]
    dates_pd = pd.DatetimeIndex(dates)
    return dates_pd.to_period("M")
    
def post_processing(
    idir,
    odir,
    release=None,
    update=None,
    prev_deck_list=None,
    overwrite=False,
):
    """Split ICOADS data into monthly deck files.
    Use this function to create obs_suite level0 data.

    Parameters
    ----------
    idir: str
        Input data directory
    odir: str
        Output data directory
    release: str, default: release_7.0
        Release name.
    update: str, default: 000000
        Update name.
    prev_deck_list: list
        List of previous level1a decks.
    overwrite: bool
        If True, overwrite already existing files.
    """
    if prev_deck_list is None:
        prev_deck_list = [Path(x).name for x in glob.glob(os.path.join(idir, "log", "*"))]
    if release is None:
        release = _release
    if update is None:
        update = _update
    
    for table in cdm_mapper.properties.cdm_tables:
        if table == "header":
            time_axis = "report_timestamp"
        else:
            time_axis = "date_time"
        for prev_deck in prev_deck_list:
            table_dir = os.path.join(idir, prev_deck)
            table_df = cdm_mapper.read_tables(table_dir, cdm_subset=table)
            if table_df.empty:
                continue
            year_month = get_year_month(table_df, time_axis)
            for ym, df in table_df.groupby(year_month):
                oname = os.path.join(odir, f"{table}-{ym}-{release}-{update}.psv")
                if not os.path.isfile(oname):
                    mode="w"
                    header=df.columns
                if os.path.isfile(oname):
                    mode="a"
                    header=None
                df.to_csv(oname, sep="|", header=header, mode=mode, index=False)
