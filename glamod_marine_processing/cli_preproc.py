"""
============================================
Pre-Processing Command Line Interface module
============================================
"""

from __future__ import annotations

import os

import click

from .cli import CONTEXT_SETTINGS, add_options
from .glamod_marine_processing import pre_processing
from .utilities import mkdir


@click.command(context_settings=CONTEXT_SETTINGS)
@add_options()
def PreProcCli(
    machine,
    dataset,
    data_directory,
    work_directory,
    overwrite,
):
    """Entry point for the pre-processing command line interface."""
    input_dir = os.path.join(data_directory, "datasets", dataset, "ORIGINAL")
    output_dir = os.path.join(data_directory, "datasets", dataset, "level0")

    mkdir(output_dir)

    pre_processing(
        idir=input_dir,
        odir=output_dir,
        overwrite=overwrite,
    )
