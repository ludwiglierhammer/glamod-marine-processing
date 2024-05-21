"""
======================================
Metadata Command Line Interface module
======================================
"""

from __future__ import annotations

import datetime
import os

import click

from .cli import Cli, CONTEXT_SETTINGS, add_options
from .utilities import get_base_path, get_configuration, load_json, mkdir, save_json


@click.command(context_settings=CONTEXT_SETTINGS)
@add_options()
def MdataCli(
    machine,
    release,
    previous_release,
    split_files,
    merge_countries,
    extract_for_cds,
    data_directory,
    work_directory,
    config_file,
    submit_jobs,
):
    """Enry point for the metadata_suite command line interface."""

    def execute_command(slurm_script, add=""):
        """Run bash command."""
        slurm_script = os.path.join(lotus_scripts_directory, slurm_script)
        bash_command = f"{slurm_script} {scripts_directory} {code_directory} {release_directory} {new_config} {add}"

        if submit_jobs is True:
            os.system(f"sbatch {bash_command}")
        else:
            os.system(f"bash {bash_command}")

    config = Cli(
        machine=machine,
        level="",
        release=release,
        update="",
        dataset="",
        data_directory=data_directory,
        work_directory=work_directory,
        config_file=config_file,
        suite="metadata_suite",
    ).initialize()
    return
    home_directory = get_base_path()
    data_directory = config["paths"]["data_directory"]
    code_directory = os.path.join(home_directory, "metadata_suite")
    config_directory = os.path.join(code_directory, "config")
    scripts_directory = os.path.join(code_directory, "scripts")
    lotus_scripts_directory = os.path.join(code_directory, "lotus_scripts")
    work_directory = os.path.abspath(config["paths"]["glamod"])
    scratch_directory = os.path.join(work_directory, os.getlogin())
    
    
    release_directory = os.path.join(scratch_directory, "metadata_suite")
    log_directory = os.path.join(release_directory, "logs")
    log2_directory = os.path.join(release_directory, "logs2")
    mkdir(os.path.join(log_directory, "failed"))
    mkdir(os.path.join(log_directory, "successful"))
    mkdir(os.path.join(log2_directory, "failed"))
    mkdir(os.path.join(log2_directory, "successful"))

    lotus_config_file = "config_lotus.json"
    lotus_config_file = os.path.join(config_directory, lotus_config_file)
    lotus_config = load_json(lotus_config_file)
    lotus_config["data_path"] = os.path.join(data_directory, previous_release, "Pub47")
    lotus_config["config_path"] = config_directory
    lotus_config["output_path"] = os.path.join(
        release_directory, "data", "wmo_publication_47"
    )
    lotus_config["mapping_path"] = os.path.join(config_directory, "mapping")
    current_time = datetime.datetime.now()
    current_time = current_time.strftime("%Y%m%dT%H%M%S")

    new_config = f"config_lotus_{current_time}.json"
    new_config = os.path.join(release_directory, new_config)
    mkdir(release_directory)
    save_json(lotus_config, new_config)

    if split_files is True:
        execute_command("submit_split.sh", add=log2_directory)

    if merge_countries is True:
        execute_command("submit_merge.sh")

    if extract_for_cds is True:
        execute_command("submit_extract.sh")
