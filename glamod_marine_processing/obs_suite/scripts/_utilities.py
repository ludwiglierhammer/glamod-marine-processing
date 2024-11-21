"""Utility functions/classes for level scripts."""

from __future__ import annotations

import datetime
import glob
import itertools
import json
import logging
import os
import sys

delimiter = "|"
FFS = "-"

add_data_paths = {
    "level1a": ["level_excluded_path", "level_invalid_path"],
    "level1b": [],
    "level1c": ["level_invalid_path"],
    "level1d": ["level_log_path"],
    "level1e": ["level_log_path"],
    "level2": ["level_excluded_path", "level_reports_path"],
}

chunksizes = {
    "C-RAID_1.2": None,
    "ICOADS_R3.0.2T": 200000,
    "ICOADS_R3.0.0T": 200000,
}


# Functions--------------------------------------------------------------------
class script_setup:
    """Create script."""

    def __init__(self, process_options, inargs, clean=False):
        configfile = inargs[1]

        try:
            with open(configfile) as fileObj:
                config = json.load(fileObj)
                self.config = config
        except Exception:
            logging.error(f"Opening configuration file: {configfile}", exc_info=True)
            self.flag = False
            return

        if len(sys.argv) >= 8:
            logging.warning(
                "Removed option to provide sid_dck, year and month as arguments. Use config file instead"
            )
        self.dataset = config["abbreviations"].get("dataset")

        sid_dck = config.get("sid_dck")
        self.sid_dck = sid_dck
        self.year = config.get("yyyy")
        self.month = config.get("mm")

        if "-" in sid_dck:
            self.dck = sid_dck.split("-")[1]
        else:
            self.dck = sid_dck
        self.corrections = config.get("corrections")

        try:
            for opt in process_options:
                if not config.get(sid_dck, {}).get(opt):
                    setattr(self, opt, config.get(opt))
                else:
                    setattr(self, opt, config.get(sid_dck).get(opt))
            self.flag = True
        except Exception:
            logging.error(
                f"Parsing configuration from file: {configfile}", exc_info=True
            )
            self.flag = False

        self.data_path = config["paths"].get("data_directory")
        self.release = config["abbreviations"].get("release")

        self.filename = config.get("filename")
        self.level2_list = config.get("cmd_add_file")
        self.prev_fileID = config.get("prev_fileID")
        self.release_id = config["abbreviations"].get("release_tag")
        self.fileID = FFS.join(
            [str(self.year), str(self.month).zfill(2), self.release_id]
        )
        self.fileID_date = FFS.join([str(self.year), str(self.month)])
        if self.prev_fileID is None:
            self.prev_fileID = self.fileID

        self.prev_level_path = os.path.join(
            config["paths"]["source_directory"], sid_dck
        )
        level_path = config["paths"]["destination_directory"]
        self.level_path = os.path.join(level_path, sid_dck)
        self.level_ql_path = os.path.join(level_path, "quicklooks", sid_dck)
        self.level_log_path = os.path.join(level_path, "log", sid_dck)
        self.level_invalid_path = os.path.join(level_path, "invalid", sid_dck)
        self.level_excluded_path = os.path.join(level_path, "excluded", sid_dck)
        self.level_reports_path = os.path.join(level_path, "reports", sid_dck)
        data_paths = [
            self.prev_level_path,
            self.level_path,
            self.level_ql_path,
        ]
        for data_path in add_data_paths[config["level"]]:
            data_paths.append(getattr(self, data_path))
        paths_exist(data_paths)

        if len(glob.glob(self.filename)) == 0:
            logging.error(f"Previous level header files not found: {self.filename}")
            sys.exit(1)

        filenames = [
            glob.glob(f"{data_path}/**/*", recursive=True)
            for data_path in data_paths[1:]
        ]

        if clean is True:
            clean_level(filenames)


# This is for json to handle dates
def date_handler(obj):
    """Handle date."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()


def table_to_csv(df, out_name, **kwargs):
    """Write table to disk."""
    if len(df) == 0:
        return
    df.to_csv(
        out_name,
        index=False,
        sep=delimiter,
        header=True,
        mode="w",
        na_rep="null",
        **kwargs,
    )


def clean_level(filenames):
    """Clean level."""
    filenames = list(itertools.chain(*filenames))
    for filename in filenames:
        try:
            logging.info(f"Removing previous file: {filename}")
            os.remove(filename)
        except Exception:
            logging.warning(f"Could not remove previous file: {filename}")
            pass


def paths_exist(data_paths):
    """Check whether path(s) exist(s)."""
    if not isinstance(data_paths, list):
        data_paths = [data_paths]
    exit = False
    for data_path in data_paths:
        if not os.path.isdir(data_path):
            exit = True
            logging.error(f"Could not find data paths: {data_path}")
    if exit is True:
        sys.exit(1)
