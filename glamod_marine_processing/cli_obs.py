"""
===========================================
Observational Command Line Interface module
===========================================
"""
from __future__ import annotations

import datetime
import os
import shutil
from types import SimpleNamespace

import click

from .cli import CONTEXT_SETTINGS, Cli, add_options
from .utilities import add_to_config, load_json, save_json


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
    config_file,
    submit_jobs,
):
    """Enry point for the obs_suite command line interface."""
    config = Cli(
        machine=machine,
        level=level,
        release=release,
        update=update,
        dataset=dataset,
        data_directory=data_directory,
        work_directory=work_directory,
        config_file=config_file,
        suite="obs_suite",
    ).initialize()

    p = SimpleNamespace(**config["paths"])
    slurm_script = "level_slurm.py"
    slurm_script_ = f"{level}_slurm.py"
    slurm_script_tmp = os.path.join(p.lotus_scripts_directory, slurm_script)
    slurm_script_new = os.path.join(p.release_directory, slurm_script_)
    shutil.copyfile(slurm_script_tmp, slurm_script_new)

    level_config_file = f"{level}.json"
    level_config_file = os.path.join(p.config_files_path, level_config_file)

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
    new_config = os.path.join(p.release_directory, new_config)
    save_json(level_config, new_config)
    os.system(f"python {slurm_script_new} {new_config}")
