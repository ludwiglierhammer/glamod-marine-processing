"""
=============================================
Quality control Command Line Interface module
=============================================
"""

from __future__ import annotations

import os

import click

from .utilities import get_base_path, get_configuration, mkdir


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
    "-u", "--update", default="000000", help="Name of the data release update."
)
@click.option(
    "-d",
    "--dataset",
    default="ICOADS_R3.0.2T",
    help="Name of the data release dataset.",
)
@click.option(
    "-c",
    "--corrections_version",
    default="",
    help="Name of the NOC corrections version.",
)
@click.option("-submit", "--submit_jobs", is_flag=True, help="Submit job scripts")
def QcCli(
    machine,
    release,
    update,
    dataset,
    corrections_version,
    submit_jobs,
):
    """Enry point for theqcmetadata_suite command line interface."""
    config = get_configuration(machine)

    home_directory = get_base_path()
    data_directory = config["paths"]["data_directory"]
    code_directory = os.path.join(home_directory, "qc_suite")
    obs_code_directory = os.path.join(home_directory, "obs_suite")
    configuration_directory = os.path.join(
        obs_code_directory, "configuration_files", release, dataset
    )
    # config_directory = os.path.join(code_directory, "config")
    scripts_directory = os.path.join(code_directory, "scripts")
    lotus_scripts_directory = os.path.join(code_directory, "lotus_scripts")
    work_directory = os.path.abspath(config["paths"]["glamod"])
    scratch_directory = os.path.join(work_directory, os.getlogin())
    release_directory = os.path.join(scratch_directory, "qc_suite")

    mkdir(os.path.join(release_directory, "logs_qc"))
    mkdir(os.path.join(release_directory, "logs_qc_hr"))

    qc_source = os.path.join(data_directory, release, dataset, "level1d")
    dck_list = os.path.join(configuration_directory, "source_deck_list.txt")
    dck_period = os.path.join(configuration_directory, "source_deck_periods.json")
    corrections = os.path.join(
        data_directory, release, "NOC_corrections", corrections_version
    )
    qc_destination = os.path.join(data_directory, release, "metoffice_qc", "corrected")

    slurm_script = "preprocess.py"
    slurm_script = os.path.join(scripts_directory, slurm_script)

    os.system(
        "python {} -source={} -dck_list={} -dck_period={} -corrections={} -destination={} -release={} -update={}".format(
            slurm_script,
            qc_source,
            dck_list,
            dck_period,
            corrections,
            qc_destination,
            release,
            update,
        )
    )

    slurm_script = "qc_slurm.py"
    slurm_script = os.path.join(lotus_scripts_directory, slurm_script)
    os.system("python {slurm_script} qc_config.txt")

    slurm_script = "qc_hr_slurm.py"
    slurm_script = os.path.join(lotus_scripts_directory, slurm_script)
    os.system("python {slurm_script} qc_config.txt")
