"""GLAMOD marine processing auxiliray functions."""

from __future__ import annotations

import errno
import json
import os

try:
    from importlib.resources import files as _files
except ImportError:
    from importlib_resources import files as _files


_base = "glamod_marine_processing"

config_files = {
    "kay": "config_kay.json",
    "meluxina": "config_meluxina.json",
    "test": "config_test.json",
}

PERIODS_FILE = "source_deck_periods.json"
level_subdirs = {
    "level1a": ["log", "quicklooks", "invalid", "excluded"],
    "level1b": ["log", "quicklooks"],
    "level1c": ["log", "quicklooks", "invalid"],
    "level1d": ["log", "quicklooks"],
    "level1e": ["log", "quicklooks", "reports"],
    "level2": ["log", "quicklooks", "excluded", "reports"],
    "metadata_suite": ["log", "log2"],
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
    release_periods_file = os.path.join(
        config_path, release, update, dataset, PERIODS_FILE
    )
    sid_dck_dict = load_json(release_periods_file)

    level_subdirs_ = level_subdirs[level]
    level_subdirs_.extend(".")

    # CREATE DIRS
    release_path = os.path.join(data_path, release)
    source_path = os.path.join(release_path, dataset)
    level_subdir = os.path.join(source_path, level)
    for sublevel in level_subdirs_:
        create_subdir(os.path.join(level_subdir, sublevel), sid_dck_dict.keys())


def add_to_config(config, key=None, **kwargs):
    """Add arguments to configuration file."""
    for k, v in kwargs.items():
        if key:
            if key not in config.keys():
                config[key] = {}
            config[key][k] = v
        else:
            config[k] = v
    return config


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


def get_base_path():
    """Get files from file path."""
    return os.path.abspath(_files(_base))


def get_configuration(machine):
    """Get machine-depending configuration file."""
    _base_path = get_base_path()
    machine = machine.lower()
    try:
        config_file = config_files[machine]
    except KeyError:
        raise KeyError(
            "{} is not a valid machine name. Use one of {} instead.".format(
                machine,
                list(config_files.keys()),
            )
        )
    config_file = os.path.join(_base_path, "configuration_files", config_file)
    return load_json(config_file)
