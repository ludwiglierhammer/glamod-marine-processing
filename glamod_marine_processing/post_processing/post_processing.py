"""Split original ICOADS data into monthly source and deck files."""

from __future__ import annotations

import glob
import os
import subprocess
from itertools import chain
from pathlib import Path

import pandas as pd
from cdm_reader_mapper import cdm_mapper


def get_year_month(df, time_axis):
    """Group dataframe by year-month."""
    dates = df[time_axis]
    dates_pd = pd.DatetimeIndex(dates)
    return dates_pd.to_period("M")


def get_file_dict(file_list):
    """Convert data file list to data file dict. Keys: file names."""
    file_dict = {}
    for ifile in file_list:
        ifile_name = Path(ifile).name
        if ifile_name in file_dict.keys():
            file_dict[ifile_name].append(ifile)
        else:
            file_dict[ifile_name] = [ifile]
    return file_dict


def concat_open_files(idir, odir, table, release, update, prev_deck_list):
    """Open files and concat them."""
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
            header = None
            mode = "a"
            if not os.path.isfile(oname):
                mode = "w"
                header = df.columns
            df.to_csv(oname, sep="|", header=header, mode=mode, index=False)


def concat_closed_files(idir, odir, table, release, update, prev_deck_list):
    """Concat file with subprocess."""
    file_list = [
        glob.glob(os.path.join(idir, prev_deck, "*")) for prev_deck in prev_deck_list
    ]
    file_list = list(chain(*file_list))
    file_dict = get_file_dict(file_list)
    for name, flist in file_dict.items():
        subprocess.call(
            ["/bin/cat"] + flist + [">", os.path.join(odir, name)], shell=False
        )


def post_processing(
    idir,
    odir,
    release=None,
    update=None,
    prev_deck_list=None,
    date_avail=False,
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
    release: str
        Release name.
    update: str
        Update name.
    prev_deck_list: list
        List of previous level1a decks.
    date_avail, bool
        Set True if date information is in file names.
    overwrite: bool
        If True, overwrite already existing files.
    """
    if prev_deck_list is None:
        prev_deck_list = [
            Path(x).name for x in glob.glob(os.path.join(idir, "log", "*"))
        ]

    for table in cdm_mapper.properties.cdm_tables:
        if date_avail is True:
            concat_closed_files(
                idir=idir,
                odir=odir,
                table=table,
                release=release,
                update=update,
                prev_deck_list=prev_deck_list,
            )
        else:
            concat_open_files(
                idir=idir,
                odir=odir,
                table=table,
                release=release,
                update=update,
                prev_deck_list=prev_deck_list,
            )
