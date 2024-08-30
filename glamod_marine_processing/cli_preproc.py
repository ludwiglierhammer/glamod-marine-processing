"""
============================================
Pre-Processing Command Line Interface module
============================================
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import click

from .cli import CONTEXT_SETTINGS, Cli, add_options
from .pre_processing import pre_processing
from .utilities import mkdir


@click.command(context_settings=CONTEXT_SETTINGS)
@add_options()
def PreProcCli(
    machine,
    dataset,
    data_directory,
    source_pattern,
    overwrite,
):
    """Entry point for the pre-processing command line interface."""  
    config = Cli(
        machine=machine,
        dataset=dataset,
        data_directory=data_directory,
    ).initialize()   
    p = SimpleNamespace(**config["paths"])  
    input_dir = os.path.join(p.data_directory, "datasets", dataset, "ORIGINAL")
    output_dir = os.path.join(p.data_directory, "datasets", dataset, "level0")
    mkdir(output_dir)

    pre_processing(
        idir=input_dir,
        odir=output_dir,
        source_pattern=source_pattern,
        overwrite=overwrite,
    )
