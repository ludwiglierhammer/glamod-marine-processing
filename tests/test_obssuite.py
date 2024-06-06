from __future__ import annotations

import os

import subprocess

import cdm_reader_mapper as cdm  # noqa
import pytest  # noqa

import glamod_marine_processing  # noqa
from glamod_marine_processing.cli_obs import ObsCli

from click.testing import CliRunner

from cdm_reader_mapper.common.getting_files import load_file

def test_level1a():
    """Testing level1a."""
    load_file(
        f"imma1_992/input/114-992_2016-01-01_subset.imma",
        cache_dir=f"./datasets/ICOADS_R3.0.0T/level0/114-992",
        within_drs=False,
    )
    #runner = CliRunner()
    #result = runner.invoke(ObsCli, ["-l level1a -r release_test -d ICOADS_R3.0.0T -data_dir . -work_dir ."])
    #result = runner.run(ObsCli, ["-l level1a -r release_test -d ICOADS_R3.0.0T -data_dir . -work_dir ."])
    #result = runner.invoke(ObsCli, ['-h'])
    #print(result.output)
    #print(result.stderr)
    #print(result.stdout)
    #subprocess.run(["obs_suite -l level1a -r release_test -d ICOADS_R3.0.0T -data_dir . -work_dir ."], shell=True)
    subprocess.run("obs_suite -h", shell=True, check=True, capture_output=True)
test_level1a()    
#def test_level1a_NRT():
#    """Testing level1a."""
#    load_file(
#        f"{dm}_{deck}/input/{data_file}",
#        cache_dir=f"./datasets/ICOADS_R3.0.2T/level0/171-711",
#    )

def test_level1b():
    """Testing level1b."""


def test_level1c():
    """Testing level1c."""


def test_level1d():
    """Testing level1d."""


def test_level1e():
    """Testing level1e."""


def test_level2():
    """Testing level2."""
