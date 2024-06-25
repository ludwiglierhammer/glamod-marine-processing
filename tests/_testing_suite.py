from __future__ import annotations

import os

import _load_data
import _settings
import pandas as pd
from cdm_reader_mapper.cdm_mapper import cdm_to_ascii, read_tables
from cdm_reader_mapper.common.getting_files import load_file

add_data = {
    "level1a": None,
    "level1b": _load_data.load_NOC_corrections,
    "level1c": _load_data.load_NOC_ANC_INFO,
    "level1d": _load_data.load_Pub47,
    "level1e": _load_data.load_metoffice_qc,
    "level2": None,
}


def manipulate_expected(expected, level):
    """Manipulate expected result data."""
    for index, values in _settings.manipulation[level].items():
        expected[index] = values
    return expected


def _obs_testing(level, capsys):
    """Observational testing suite."""
    tables = _settings.which_tables[level]
    if add_data[level] is not None:
        add_data[level](
            cache_dir=f"./T{level}/release_7.0",
        )

    cache_dir = _load_data.load_input(level)

    s = (
        "obs_suite "
        f"-l {level} "
        f"-data_dir ./T{level} "
        f"-work_dir ./T{level} "
        f"-sp {_settings.pattern[level]} "
        "-p_id subset "
        "-o "
        "-run"
    )
    os.system(s)
    captured = capsys.readouterr()
    assert captured.out == ""

    results = read_tables(
        f"./T{level}/release_7.0/ICOADS_R3.0.2T/{level}/114-992", cdm_subset=tables
    )
    for table_name in tables:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir=f"./E{level}/ICOADS_R3.0.2T/{level}/114-992",
            within_drs=False,
        )
    expected = read_tables(
        f"./E{level}/ICOADS_R3.0.2T/{level}/114-992", cdm_subset=tables
    )

    expected = manipulate_expected(expected, level)

    for deletion in [("header", "record_timestamp"), ("header", "history")]:
        del results[deletion]
        del expected[deletion]

    pd.testing.assert_frame_equal(results, expected)
