"""Utility functions/classes for level scripts."""

from __future__ import annotations

import datetime
import glob
import json
import logging
import os
import sys

delimiter = "|"
FFS = "-"


# Functions--------------------------------------------------------------------
class script_setup:
    """Create script."""

    def __init__(self, process_options, inargs, level, level_prev):
        self.data_path = inargs[1]
        self.release = inargs[2]
        self.update = inargs[3]
        self.dataset = inargs[4]
        self.configfile = inargs[5]

        try:
            with open(self.configfile) as fileObj:
                config = json.load(fileObj)
        except Exception:
            logging.error(
                f"Opening configuration file :{self.configfile}", exc_info=True
            )
            self.flag = False
            return

        if len(sys.argv) >= 8:
            logging.warning(
                "Removed option to provide sid_dck, year and month as arguments. Use config file instead"
            )
        if len(sys.argv) > 6:
            self.sid_dck = inargs[6]
            self.year = inargs[7]
            self.month = inargs[8]
        else:
            self.sid_dck = config.get("sid_dck")
            self.year = config.get("yyyy")
            self.month = config.get("mm")

        self.dck = self.sid_dck.split("-")[1]
        self.corrections = config.get("corrections")

        try:
            for opt in process_options:
                if not config.get(self.sid_dck, {}).get(opt):
                    setattr(self, opt, config.get(opt))
                else:
                    setattr(self, opt, config.get(self.sid_dck).get(opt))
            self.flag = True
        except Exception:
            logging.error(
                f"Parsing configuration from file :{self.configfile}", exc_info=True
            )
            self.flag = False

        self.filename = config.get("filename")
        self.level2_list = config.get("cmd_add_file")
        self.prev_fileID = config.get("prev_fileID")
        release_path = os.path.join(self.data_path, self.release, self.dataset)
        self.release_id = FFS.join([self.release, self.update])
        self.fileID = FFS.join(
            [str(self.year), str(self.month).zfill(2), self.release_id]
        )
        self.fileID_date = FFS.join([str(self.year), str(self.month)])
        if self.prev_fileID is None:
            self.prev_fileID = self.fileID

        self.prev_level_path = os.path.join(release_path, level_prev, self.sid_dck)
        self.level_path = os.path.join(release_path, level, self.sid_dck)
        self.level_ql_path = os.path.join(
            release_path, level, "quicklooks", self.sid_dck
        )
        self.level_log_path = os.path.join(
            self.release_path, level, "log", self.sid_dck
        )
        self.level_invalid_path = os.path.join(
            release_path, level, "invalid", self.sid_dck
        )
        self.level_excluded_path = os.path.join(
            release_path, level, "excluded", self.sid_dck
        )
        self.level_reports_path = os.path.join(
            release_path, level, "reports", self.sid_dck
        )
        data_paths = [self.prev_level_path, self.level_path, self.level_ql_path, self.level_log_path, self.level_invalid_path, self.level_excluded_path]

        if any([not os.path.isdir(x) for x in data_paths]):
            logging.error(
                "Could not find data paths: {}".format(
                    ",".join([x for x in data_paths if not os.path.isdir(x)])
                )
            )
            sys.exit(1)

        if len(glob.glob(self.filename)) == 0:
            logging.error(f"L1b header files not found: {self.filename}")
            sys.exit(1)


# This is for json to handle dates
def date_handler(obj):
    """Handle date."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()


def table_to_csv(df, out_name, **kwargs):
    """Write table to disk."""
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
    for filename in filenames:
        try:
            logging.info(f"Removing previous file: {filename}")
            os.remove(filename)
        except Exception:
            logging.warning(f"Could not remove previous file: {filename}")
            pass
