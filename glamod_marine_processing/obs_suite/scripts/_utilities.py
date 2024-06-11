"""Utility functions/classes for level scripts."""

from __future__ import annotations

import datetime
import json
import logging
import sys


# Functions--------------------------------------------------------------------
class script_setup:
    """Create script."""

    def __init__(self, process_options, inargs):
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


# This is for json to handle dates
def date_handler(obj):
    """Handle date."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
