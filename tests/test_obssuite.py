from __future__ import annotations

import json
import os

import pandas as pd
from cdm_reader_mapper.cdm_mapper import read_tables
from cdm_reader_mapper.common.getting_files import load_file

from glamod_marine_processing.utilities import mkdir

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

table_names_1b = [
    "header",
    "observations-at",
    "observations-dpt",
    "observations-slp",
    "observations-sst",
    "observations-wd",
    "observations-ws",
]


def _load_NOC_corrections(**kwargs):
    for sub in [
        "duplicate_flags",
        "duplicates",
        "id",
        "latitude",
        "longitude",
        "timestamp",
    ]:
        load_file(
            f"NOC_corrections/v1x2023/{sub}/2022-01.txt.gz",
            **kwargs,
        )


def _load_NOC_ANC_INFO(**kwargs):
    load_file(
        "NOC_ANC_INFO/json_files/dck992.json",
        **kwargs,
    )


def _load_Pub47(**kwargs):
    load_file(
        "Pub47/monthly/2022-01-01.json",
        **kwargs,
    )


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
            cache_dir="./E1A/ICOADS_R3.0.2T/level1a/114-992",
            within_drs=False,
        )
    expected = read_tables("./E1A/ICOADS_R3.0.2T/level1a/114-992")

    del results[("header", "record_timestamp")]
    del expected[("header", "record_timestamp")]
    del results[("header", "history")]
    del expected[("header", "history")]

    pd.testing.assert_frame_equal(results, expected)


def test_level1b(capsys):
    """Testing level1b."""
    _load_NOC_corrections(
        cache_dir="./T1B/release_7.0",
        branch="marine_processing_testing",
    )
    for table_name in table_names:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir="./T1B/release_7.0/ICOADS_R3.0.2T/level1a/114-992",
            within_drs=False,
        )
    s = (
        "obs_suite "
        "-l level1b "
        "-data_dir ./T1B "
        "-work_dir ./T1B "
        "-sp header-???-???_????-??-??_subset.psv "
        "-o "
        "-run"
    )
    os.system(s)
    captured = capsys.readouterr()
    assert captured.out == ""

    results = read_tables(
        "./T1B/release_7.0/ICOADS_R3.0.2T/level1b/114-992", cdm_subset=table_names_1b
    )

    for table_name in table_names_1b:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir="./E1B/ICOADS_R3.0.2T/level1b/114-992",
            within_drs=False,
        )
    expected = read_tables(
        "./E1B/ICOADS_R3.0.2T/level1b/114-992", cdm_subset=table_names_1b
    )

    del results[("header", "record_timestamp")]
    del expected[("header", "record_timestamp")]
    del results[("header", "history")]
    del expected[("header", "history")]

    pd.testing.assert_frame_equal(results, expected)


def test_level1c(capsys):
    """Testing level1c."""
    _load_NOC_ANC_INFO(
        cache_dir="./T1C/release_7.0",
        branch="marine_processing_testing",
    )
    for table_name in table_names:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir="./T1C/release_7.0/ICOADS_R3.0.2T/level1b/114-992",
            within_drs=False,
        )

    s = (
        "obs_suite "
        "-l level1c "
        "-data_dir ./T1C "
        "-work_dir ./T1C "
        "-sp header-???-???_????-??-??_subset.psv "
        "-o "
        "-run"
    )
    os.system(s)
    captured = capsys.readouterr()
    assert captured.out == ""

    results = read_tables(
        "./T1C/release_7.0/ICOADS_R3.0.2T/level1c/114-992", cdm_subset=["header"]
    )
    for table_name in table_names_1b:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir="./E1C/ICOADS_R3.0.2T/level1c/114-992",
            within_drs=False,
        )
    expected = read_tables(
        "./E1C/ICOADS_R3.0.2T/level1c/114-992", cdm_subset=["header"]
    )

    del results["record_timestamp"]
    del expected["record_timestamp"]
    del results["history"]
    del expected["history"]

    pd.testing.assert_frame_equal(results, expected)


def test_level1d(capsys):
    """Testing level1d."""
    _load_Pub47(
        cache_dir="./T1D/release_7.0",
        branch="marine_processing_testing",
    )
    for table_name in table_names:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir="./T1D/release_7.0/ICOADS_R3.0.2T/level1c/114-992",
            within_drs=False,
        )

    s = (
        "obs_suite "
        "-l level1d "
        "-data_dir ./T1D "
        "-work_dir ./T1D "
        "-sp header-???-???_????-??-??_subset.psv "
        "-o "
        "-run"
    )
    os.system(s)
    captured = capsys.readouterr()
    assert captured.out == ""

    results = read_tables(
        "./T1D/release_7.0/ICOADS_R3.0.2T/level1d/114-992", cdm_subset=["header"]
    )
    for table_name in table_names_1b:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir="./E1D/ICOADS_R3.0.2T/level1c/114-992",
            within_drs=False,
        )
    expected = read_tables(
        "./E1D/ICOADS_R3.0.2T/level1d/114-992", cdm_subset=["header"]
    )

    del results["record_timestamp"]
    del expected["record_timestamp"]
    del results["history"]
    del expected["history"]

    pd.testing.assert_frame_equal(results, expected)


def test_level1e():
    """Testing level1e."""


def test_level2():
    """Testing level2."""
