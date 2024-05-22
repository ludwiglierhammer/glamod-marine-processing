"""
========================================
Marine processing Command Line Interface
========================================
"""

from __future__ import annotations

import os

import click

from .utilities import (
    add_to_config,
    get_abs_path,
    get_base_path,
    get_configuration,
    load_json,
    make_release_source_tree,
    mkdir,
)

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], show_default=True)


def add_options():
    """Add decorator click options."""

    def _get_parameters(func):
        argcount = func.__code__.co_argcount
        return func.__code__.co_varnames[:argcount]

    def _add_options(func):
        options = _get_parameters(func)
        for option in reversed(options):
            if not hasattr(Options, option):
                continue
            option = getattr(Options, option)
            func = option(func)
        return func

    return _add_options


class Cli:
    """Skeleton command line interface class."""

    def __init__(
        self,
        machine,
        level,
        release,
        update,
        dataset,
        data_directory,
        work_directory,
        config_file,
        suite,
    ):
        self.machine = machine
        self.level = level
        self.release = release
        self.update = update
        self.dataset = dataset
        self.data_directory = data_directory
        self.work_directory = work_directory
        self.config_file = config_file
        self.suite = suite
        self.release_update = f"{release}-{update}"

    def initialize(self):
        """Initialize command line interface settings."""
        if not self.config_file:
            # config = get_configuration(self.machine)
            config = self.build_configuration()
        elif not os.path.isfile(self.config_file):
            raise FileNotFoundError(config)
        else:
            config = load_json(self.config_file)

        make_release_source_tree(
            data_path=config["paths"]["data_directory"],
            config_path=config["paths"]["config_directory"],
            release=self.release,
            update=self.update,
            dataset=self.dataset,
            level=self.level,
        )
        mkdir(config["paths"]["release_directory"])
        return config

    def build_configuration(self):
        """Build configuration."""
        config = get_configuration(self.machine)
        config["abbreviations"] = {
            "release": self.release,
            "update": self.update,
            "dataset": self.dataset,
            "release_tag": self.release_update,
        }

        if self.data_directory is not None:
            config["paths"]["data_directory"] = self.data_directory
        if self.work_directory is not None:
            config["paths"]["glamod"] = self.work_directory

        config["paths"]["data_directory"] = get_abs_path(
            config["paths"]["data_directory"]
        )
        config["paths"]["glamod"] = get_abs_path(config["paths"]["glamod"])

        home_directory = get_base_path()
        code_directory = os.path.join(home_directory, self.suite)
        config_directory = os.path.join(code_directory, "configuration_files")
        config_files_path = os.path.join(
            config_directory, self.release, self.update, self.dataset
        )
        scripts_directory = os.path.join(code_directory, "scripts")
        lotus_scripts_directory = os.path.join(code_directory, "lotus_scripts")
        work_directory = os.path.abspath(config["paths"]["glamod"])
        scratch_directory = os.path.join(work_directory, os.getlogin())
        release_directory = os.path.join(
            scratch_directory, self.release, self.dataset, self.level
        )

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
        return config


class Options:
    """Class for click options."""

    def __init__(self):
        self.machine = click.option(
            "-m",
            "--machine",
            default="MELUXINA",
            help="""HPC cluster where to create and run the scripts, \n
            * KAY: kay.ichec.ie \n
            * MELUXINA: login.lxp.lu
            """,
        )
        self.submit_jobs = click.option(
            "-submit", "--submit_jobs", is_flag=True, help="Submit job scripts"
        )
        self.level = click.option(
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
        self.release = click.option(
            "-r", "--release", default="release_7.0", help="Name of the data release."
        )
        self.update = click.option(
            "-u", "--update", default="000000", help="Name of the data release update."
        )
        self.dataset = click.option(
            "-d",
            "--dataset",
            default="ICOADS_R3.0.2T",
            help="Name of the data release dataset.",
        )
        self.previous_release = click.option(
            "-pr",
            "--previous_release",
            default="release_6.0",
            help="Name of the previous data release.",
        )
        self.data_directory = click.option(
            "-data_dir",
            "--data_directory",
            help="Directory path of the input and output datasets. By default, take directory path from machine-depending configuration file.",
        )
        self.work_directory = click.option(
            "-work_dir",
            "--work_directory",
            help="Directory path of the log and template files. By default, take directory path from machine-depending configuration file.",
        )
        self.split_files = click.option(
            "-split",
            "--split_files",
            is_flag=True,
            help="Step 1: Splitting PUB47 data files.",
        )
        self.merge_countries = click.option(
            "-merge", "--merge_countries", is_flag=True, help="Step 2: Merge countries."
        )
        self.extract_for_cds = click.option(
            "-extract",
            "--extract_for_cds",
            is_flag=True,
            help="Step 3: Extract for CDS",
        )
        self.corrections_version = click.option(
            "-c",
            "--corrections_version",
            default="v1x2023",
            help="Name of the NOC corrections version.",
        )
        self.config_file = click.option(
            "-cfg",
            "--config_file",
            default=False,
            help="Use already existing configuration file.",
        )


Options = Options()
