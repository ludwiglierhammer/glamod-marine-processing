from __future__ import annotations

import os
import subprocess

import cdm_reader_mapper as cdm
import pytest  # noqa
from cdm_reader_mapper.common.getting_files import load_file
from click.testing import CliRunner

import glamod_marine_processing
from glamod_marine_processing.cli_obs import ObsCli


def test_level1a_NRT():
    """Testing level1a."""
    load_file(
        f"imma1_992/input/114-992_2022-01-01_subset.imma",
        cache_dir=f"./datasets/ICOADS_R3.0.2T/level0/114-992",
        within_drs=False,
    )
    s = (
        "obs_suite "
        "-l level1a "
        "-data_dir . "
        "-work_dir . "
        "-sp ???-???_????-??-??_subset.imma "
        "-o "
        "-run"
    )
    os.system(s)


test_level1a_NRT()


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
