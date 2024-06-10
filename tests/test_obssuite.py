from __future__ import annotations

import os

import pandas as pd
from cdm_reader_mapper.cdm_mapper import read_tables
from cdm_reader_mapper.common.getting_files import load_file

table_names = [
    "header",
    "observations-at",
    "observations-dpt",
    "observations-slp",
    "observations-sst",
    "observations-wbt",
    "observations-wd",
    "observations-ws",
]


def test_level1a(capsys):
    """Testing level1a."""
    load_file(
        "imma1_992/input/114-992_2022-01-01_subset.imma",
        cache_dir="./T1A/datasets/ICOADS_R3.0.2T/level0/114-992",
        within_drs=False,
    )
    s = (
        "obs_suite "
        "-l level1a "
        "-data_dir ./T1A "
        "-work_dir ./T1A "
        "-sp ???-???_????-??-??_subset.imma "
        "-o "
        "-run"
    )
    os.system(s)
    captured = capsys.readouterr()
    assert captured.out == ""

    results = read_tables("./T1A/release_7.0/ICOADS_R3.0.2T/level1a/114-992")
    for table_name in table_names:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir="./expected/ICOADS_R3.0.2T/level1a/114-992",
            within_drs=False,
        )
    expected = read_tables("./expected/ICOADS_R3.0.2T/level1a/114-992")

    del results[("header", "record_timestamp")]
    del expected[("header", "record_timestamp")]
    del results[("header", "history")]
    del expected[("header", "history")]

    pd.testing.assert_frame_equal(results, expected)


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
