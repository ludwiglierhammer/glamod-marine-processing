#!/usr/bin/env python3
"""
Created on Mon Jul  8 12:29:06 2019

Creates the directory tree for a new C3S data release and source or for a new
source in a pre-existing release

Inargs:
-------

data_path: parent directory where tree is to be created
config_path: path to the obs-suite config directory
release: name for release directory
update_tag: tag for the release update
dataset: name for data source in directory tree

@author: iregon
"""

from __future__ import annotations

import os

from glamod_marine_processing.utilities import load_json, mkdir

PERIODS_FILE = "source_deck_periods.json"
level_subdirs = {
    "level1a": ["log", "quicklooks", "invalid", "excluded"],
    "level1b": ["log", "quicklooks"],
    "level1c": ["log", "quicklooks", "invalid"],
    "level1d": ["log", "quicklooks"],
    "level1e": ["log", "quicklooks", "reports"],
    "level2": ["log", "quicklooks", "excluded", "reports"],
}


def make_release_source_tree(
    data_path=None,
    config_path=None,
    release=None,
    update=None,
    dataset=None,
    level=None,
):
    """Make release source tree."""

    # Functions -------------------------------------------------------------------
    def create_subdir(lpath, subdir_list):
        """Create subdirectories."""
        subdir_list = [subdir_list] if isinstance(subdir_list, str) else subdir_list
        for subdir in subdir_list:
            sub_dir = os.path.join(lpath, subdir)
            mkdir(sub_dir)

    # Go --------------------------------------------------------------------------
    os.umask(0)
    # READ LIST OF SID-DCKS FOR RELEASE
    release_tag = "-".join([release, update])
    release_periods_file = os.path.join(config_path, release_tag, dataset, PERIODS_FILE)
    sid_dck_dict = load_json(release_periods_file)

    level_subdirs_ = level_subdirs[level]
    level_subdirs_.extend(sid_dck_dict.keys())

    # CREATE DIRS
    release_path = os.path.join(data_path, release_tag)
    source_path = os.path.join(release_path, dataset)
    level_subdir = os.path.join(source_path, level)

    for sublevel in level_subdirs_:
        create_subdir(os.path.join(level_subdir, sublevel), sid_dck_dict.keys())
