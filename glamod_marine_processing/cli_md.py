"""
======================================
Metadata Command Line Interface module
======================================
"""

from __future__ import annotations

import datetime
import os

import click

from .utilities import get_base_path, get_configuration, load_json, mkdir, save_json


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
    "-r", "--release", default="release_7.0", help="Name of the data release."
)
@click.option(
    "-pr",
    "--previous_release",
    default="release_6.0",
    help="Name of the previous data release.",
)
@click.option(
    "-split", "--split_files", is_flag=True, help="Step 1: Splitting PUB47 data files."
)
@click.option(
    "-merge", "--merge_countries", is_flag=True, help="Step 2: Merge countries."
)
@click.option(
    "-extract", "--extract_for_cds", is_flag=True, help="Step 3: Extract for CDS"
)
@click.option("-submit", "--submit_jobs", is_flag=True, help="Submit job scripts")
def MdataCli(
    machine,
    release,
    previous_release,
    split_files,
    merge_countries,
    extract_for_cds,
    submit_jobs,
):
    """Enry point for the metadata_suite command line interface."""
    config = get_configuration(machine)

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

    if split_files is True:
        slurm_script = "submit_split.sh"
        slurm_script = os.path.join(lotus_scripts_directory, slurm_script)
        lotus_config_file = "config_lotus.json"
        lotus_config_file = os.path.join(config_directory, lotus_config_file)
        lotus_config = load_json(lotus_config_file)
        lotus_config["data_path"] = os.path.join(
            data_directory, previous_release, "Pub47"
        )
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

        bash_command = f"{slurm_script} {scripts_directory} {code_directory} {release_directory} {log2_directory} {new_config}"
        if submit_jobs is True:
            os.system(f"sbatch {bash_command}")
        else:
            os.system(f"bash {bash_command}")

    if merge_countries is True:
        slurm_script = "submit_merge.sh"
        slurm_script = os.path.join(lotus_scripts_directory, slurm_script)
        os.system(f"bash {slurm_script}")

    if extract_for_cds is True:
        slurm_script = "submit_extract.sh"
        slurm_script = os.path.join(lotus_scripts_directory, slurm_script)
        os.system(f"bash {slurm_script}")
