"""
===========================================
Observational Command Line Interface module
===========================================
"""
from __future__ import annotations

import datetime
import os
import shutil

import click

from .cli import CONTEXT_SETTINGS, add_options
from .obs_suite.scripts.make_release_source_tree import make_release_source_tree
from .utilities import (
    add_to_config,
    get_base_path,
    get_configuration,
    load_json,
    mkdir,
    save_json,
)


@click.command(context_settings=CONTEXT_SETTINGS)
@add_options()
def ObsCli(
    machine,
    level,
    release,
    update,
    dataset,
    data_directory,
    work_directory,
    submit_jobs,
):
    """Enry point for the obs_suite command line interface."""
    release_update = f"{release}-{update}"
    config = get_configuration(machine)
    config["abbreviations"] = {
        "release": release,
        "update": update,
        "dataset": dataset,
        "release_tag": release_update,
    }
    if data_directory is not None:
        config["paths"]["data_directory"] = data_directory
    if work_directory is not None:
        config["paths"]["glamod"] = work_directory

    home_directory = get_base_path()
    data_directory = config["paths"]["data_directory"]
    code_directory = os.path.join(home_directory, "obs_suite")
    config_directory = os.path.join(code_directory, "configuration_files")
    config_files_path = os.path.join(config_directory, release_update, dataset)
    scripts_directory = os.path.join(code_directory, "scripts")
    lotus_scripts_directory = os.path.join(code_directory, "lotus_scripts")
    work_directory = os.path.abspath(config["paths"]["glamod"])
    scratch_directory = os.path.join(work_directory, os.getlogin())
    release_directory = os.path.join(scratch_directory, release, dataset, level)

    config = add_to_config(
        config,
        home_directory=home_directory,
        code_directory=code_directory,
        config_directory=config_directory,
        config_files_path=config_files_path,
        scripts_directory=scripts_directory,
        lotus_scripts_directory=lotus_scripts_directory,
        scratch_directory=scratch_directory,
        release_directory=release_directory,
        key="paths",
    )

    make_release_source_tree(
        data_path=data_directory,
        config_path=config_directory,
        release=release,
        update=update,
        dataset=dataset,
        level=level,
    )

    slurm_script = "level_slurm.py"
    slurm_script_ = f"{level}_slurm.py"
    slurm_script_tmp = os.path.join(lotus_scripts_directory, slurm_script)
    slurm_script_new = os.path.join(release_directory, slurm_script_)
    mkdir(release_directory)
    shutil.copyfile(slurm_script_tmp, slurm_script_new)

    level_config_file = f"{level}.json"
    level_config_file = os.path.join(config_files_path, level_config_file)

    config = add_to_config(
        config,
        slurm_script=slurm_script_new,
        level_config_file=level_config_file,
        machine=machine,
        key="scripts",
    )

    level_config = load_json(level_config_file)
    level_config["submit_jobs"] = submit_jobs
    level_config["level"] = level

    for key, value in config.items():
        level_config[key] = value

    current_time = datetime.datetime.now()
    current_time = current_time.strftime("%Y%m%dT%H%M%S")

    new_config = f"{level}_{current_time}.json"
    new_config = os.path.join(release_directory, new_config)
    save_json(level_config, new_config)
    os.system(f"python {slurm_script_new} {new_config}")
