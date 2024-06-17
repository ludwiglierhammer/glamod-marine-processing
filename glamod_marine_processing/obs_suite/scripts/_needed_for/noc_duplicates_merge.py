#!/usr/bin/env python3
"""
Created on Mon Jun 17 14:24:10 2019

This is to merge the duplicate files from Liz's dup identification: main file
 from first iteration, second file from second iteration after ID fixing....

Merges both files from and outputs 2 separate files: one for dup status and another for duplicates.

This is tailored to the output as it was in Autumn2019 (C3S Release1)

It is assumed that filenames are yyyy-mm.txt and pipe separated and that the second
file with additional dup info may not be available

On output, pandas.to_csv will detect compresion from filename (compression default is 'infer')
if input file is like .gz, output will also be compressed


Inargs:
-------
file1: path to main original duplicate file
file2: path to secondary duplicate file (from second iteration after ID fixing)
dir_flags: directory to output merged duplicate flags
dir_dups: diretory to output merged duplicates
------------------
.....

@author: iregon
"""
from __future__ import annotations

import logging
import os
import re
import sys
from importlib import reload

import pandas as pd

reload(logging)  # This is to override potential previous config of logging


filename_field_sep = "-"
delimiter = "|"


# Functions--------------------------------------------------------------------
class script_setup:
    """Set up scripts."""

    def __init__(self, inargs):
        self.file1 = inargs[1]
        self.file2 = inargs[2]
        self.filename = os.path.basename(self.file1)
        self.dir_flags = inargs[3]
        self.dir_dups = inargs[4]


# MAIN ------------------------------------------------------------------------

# Process input and set up some things ----------------------------------------
logging.basicConfig(
    format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
    level=logging.INFO,
    datefmt="%Y%m%d %H:%M:%S",
    filename=None,
)
if len(sys.argv) > 1:
    logging.info("Reading command line arguments")
    args = sys.argv
else:
    logging.error("Need arguments to run!")
    sys.exit(1)

params = script_setup(args)

in_files = [params.file1]
if any([not os.path.isfile(x) for x in in_files]):
    logging.error(
        "Could not find data files: {}".format(
            ",".join([x for x in in_files if not os.path.isfile(x)])
        )
    )
    sys.exit(1)

merge2 = True
if not os.path.isfile(params.file2):
    merge2 = False
    logging.warning(f"File 2 with extended duplicate info not found {params.file2}")


data_paths = [params.dir_flags, params.dir_dups]
if any([not os.path.isdir(x) for x in data_paths]):
    logging.error(
        "Could not find output data paths: {}".format(
            ",".join([x for x in data_paths if not os.path.isdir(x)])
        )
    )
    sys.exit(1)


# Do the data processing ------------------------------------------------------
columns = ["uid", "flag", "duplicates"]
dtype = {"uid": "object", "flag": "int", "duplicates": "object"}
correction_df1 = pd.read_csv(
    params.file1,
    delimiter=delimiter,
    dtype=dtype,
    header=None,
    usecols=[0, 1, 2],
    names=columns,
    quotechar=None,
    quoting=3,
)
correction_df1.set_index("uid", drop=False, inplace=True)

if merge2:
    correction_df2 = pd.read_csv(
        params.file2,
        delimiter=delimiter,
        dtype=dtype,
        header=None,
        usecols=[0, 1, 2],
        names=columns,
        quotechar=None,
        quoting=3,
    )
    correction_df2.set_index("uid", drop=False, inplace=True)

    correction_df1["newflag"] = correction_df2["flag"]
    correction_df1["flag"] = correction_df1[["flag", "newflag"]].max(axis=1)

    braces = re.compile("^{|}$")
    ends_comma = re.compile("^,|,$")
    correction_df2["duplicates"] = correction_df2["duplicates"].str.replace(braces, "")
    correction_df1["duplicates"] = correction_df1["duplicates"].str.replace(braces, "")
    correction_df1["newduplicates"] = correction_df2["duplicates"]
    correction_df1["newduplicates"].fillna("", inplace=True)
    correction_df1["duplicates"].fillna("", inplace=True)
    correction_df1["duplicates"] = (
        correction_df1["duplicates"] + "," + correction_df1["newduplicates"]
    )
    correction_df1["duplicates"] = correction_df1["duplicates"].str.replace(
        ends_comma, ""
    )
    correction_df1["duplicates"] = "{" + correction_df1["duplicates"] + "}"

correction_df1["ones"] = "1"
correction_df1["flag"] = correction_df1["flag"].astype(int)

filename = os.path.join(params.dir_dups, params.filename)
correction_df1[["uid", "duplicates", "ones"]].to_csv(
    filename, index=False, header=None, sep=delimiter
)
filename = os.path.join(params.dir_flags, params.filename)
correction_df1[["uid", "flag", "ones"]].to_csv(
    filename, index=False, header=None, sep=delimiter
)
