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


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
