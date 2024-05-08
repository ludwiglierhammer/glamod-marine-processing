"""
===========================================
Configuration Command Line Interface module
===========================================
"""

from __future__ import annotations

import os

import click

from .utilities import get_base_path, get_configuration


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
@click.option("-submit", "--submit_jobs", is_flag=True, help="Submit job scripts")
def ConfigCli(
    machine,
    submit_jobs,
):
    """Enry point for the config_suite command line interface."""
    config = get_configuration(machine)

    home_directory = get_base_path()
    data_directory = config["paths"]["data_directory"]
    code_directory = os.path.join(home_directory, "config_suite")
    config_directory = os.path.join(code_directory, "config")
    scripts_directory = os.path.join(code_directory, "scripts")
    lotus_scripts_directory = os.path.join(code_directory, "lotus_scripts")
    work_directory = os.path.abspath(config["paths"]["glamod"])
    scratch_directory = os.path.join(work_directory, os.getlogin())
    release_directory = os.path.join(scratch_directory, "config_suite")
