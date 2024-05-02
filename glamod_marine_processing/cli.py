"""
=============================
Command Line Interface module
=============================
"""

from __future__ import annotations

import datetime
import os
import shutil

import click

from .obs_suite.scripts.make_release_source_tree import make_release_source_tree
from .utilities import (
    add_to_config,
    get_base_path,
    get_configuration,
    load_json,
    mkdir,
    save_json,
)


@click.command()
@click.option(
    "-m",
    "--machine",
    default="MELUXINA",
    help="""HPC cluster where to create and run the scripts,
    * KAY: kay.ichec.ie \n
    * MELUXINA: login.lxp.lu \n
    * default: MELUXINA
    """,
)
@click.option(
    "-l",
    "--level",
    required=True,
    help="""Step of observation suite process:

    * level1a: Mapping dataset to CDM. \n
    * level1b: Improve data with corrections and/or additional information. \n
    * level1c: Perform data validation and apply data with metadata.\n
    * level1d: Enrich data with external metadata. \n
    * level1e: Add quality control flags to data. \n
    * level2: Make data ready to ingest in the database.
    """,
)
@click.option("-submit", "--submit_jobs", is_flag=True, help="Submit job scripts")
def ObsCli(machine, level, submit_jobs):
    """Enry point for the obs_suite command line interface."""
    config = get_configuration(machine)

    release = config["abbreviations"]["release"]
    update = config["abbreviations"]["update"]
    dataset = config["abbreviations"]["dataset"]
    release_update = f"{release}-{update}"

    home_directory = get_base_path()
    data_directory = config["paths"]["data_directory"]
    code_directory = os.path.join(home_directory, "obs_suite")
    config_directory = os.path.join(code_directory, "configuration_files")
    config_files_path = os.path.join(config_directory, release_update, dataset)
    pyTools_directory = os.path.join(code_directory, "modules", "python")
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
        pyTools_directory=pyTools_directory,
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
