"""GLAMOD marine processing auxiliray functions."""

from __future__ import annotations

import errno
import json
import os


def load_json(json_file):
    """Load json file from disk."""
    with open(json_file) as f:
        return json.load(f)


def save_json(json_dict, json_file):
    """Save json file on disk."""
    with open(json_file, "w") as f:
        json.dump(json_dict, f)


def read_txt(txt_file):
    """Read txt file from disk."""
    with open(txt_file) as f:
        return f.read().splitlines()


def mkdir(directory):
    """Make directory with any missing parents."""
    if os.path.isdir(directory):
        return
    try:
        os.makedirs(directory, 0o774, exist_ok=True)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
