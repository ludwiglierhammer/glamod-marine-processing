from __future__ import annotations

import pandas as pd
import pytest  # noqa
from _settings import get_settings
from cdm_reader_mapper import DataBundle, read_tables
from cdm_reader_mapper.common.getting_files import load_file

from glamod_marine_processing.qc_suite.modules.next_level_qc import (
    do_air_temperature_anomaly_check,
    do_air_temperature_climatology_plus_stdev_check,
    do_air_temperature_hard_limit_check,
    do_air_temperature_missing_value_check,
    do_air_temperature_no_normal_check,
    do_blacklist,
    do_date_check,
    do_day_check,
    do_dpt_climatology_plus_stdev_check,
    do_dpt_missing_value_check,
    do_dpt_no_normal_check,
    do_position_check,
    do_sst_anomaly_check,
    do_sst_freeze_check,
    do_sst_missing_value_check,
    do_sst_no_normal_check,
    do_supersaturation_check,
    do_time_check,
    do_wind_consistency_check,
    do_wind_hard_limit_check,
    do_wind_missing_value_check,
    humidity_blacklist,
    is_buoy,
    is_deck,
    is_drifter,
    is_ship,
    mat_blacklist,
    wind_blacklist,
)

dataset = "ICOADS_R3.0.2T"
_settings = get_settings(dataset)
cache_dir = f"./Eqc/{dataset}/qc/{_settings.deck}"
tables = [
    "header",
    "observations-at",
    "observations-dpt",
    "observations-slp",
    "observations-sst",
    "observations-wd",
    "observations-ws",
]
for table in tables:
    load_file(
        f"{_settings.input_dir}/cdm_tables/{table}-{_settings.cdm}.psv",
        cache_dir=cache_dir,
        within_drs=False,
    )

data = {}
db_tables = read_tables(cache_dir)

for table in tables:
    db_table = DataBundle()
    db_table.data = db_tables[table].copy()
    if table == "header":
        db_table.data["platform_type"] = db_table["platform_type"].astype(int)
        db_table.data["latitude"] = db_table["latitude"].astype(float)
        db_table.data["longitude"] = db_table["longitude"].astype(float)
        db_table.data["report_timestamp"] = pd.to_datetime(
            db_table["report_timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce"
        )
    else:
        db_table.data["observation_value"] = db_table["observation_value"].astype(float)

    data[table] = db_table


def test_is_buoy():
    db_ = data["header"].copy()
    results = db_.apply(
        lambda row: is_buoy(platform_type=row["platform_type"], valid_list=[4, 5, 6]),
        axis=1,
    )
    expected = pd.Series(
        [1] * 13
    )  # platform type is 2 which is not a buoy (4: moored buoy, 5: drifting buoy, 6: ice buoy)
    pd.testing.assert_series_equal(results, expected)


def test_is_drifter():
    db_ = data["header"].copy()
    results = db_.apply(
        lambda row: is_drifter(platform_type=row["platform_type"], valid_list=5), axis=1
    )
    expected = pd.Series(
        [1] * 13
    )  # platform type is 2 which is not a drfiting buoy (5: drifting buoy)
    pd.testing.assert_series_equal(results, expected)


def test_is_ship():
    db_ = data["header"].copy()
    results = db_.apply(
        lambda row: is_ship(platform_type=row["platform_type"], valid_list=2), axis=1
    )
    expected = pd.Series([0] * 13)  # platform type is 2 which is a ship
    pd.testing.assert_series_equal(results, expected)


def test_is_deck():
    # Deck is ICOADS specific.
    raise NotImplementedError


def test_do_position_check():
    db_ = data["header"].copy()
    results = db_.apply(
        lambda row: do_position_check(
            latitude=row["latitude"], longitude=row["longitude"]
        ),
        axis=1,
    )
    expected = pd.Series([0] * 13)  # all positions are valid
    pd.testing.assert_series_equal(results, expected)


def test_do_date_check():
    db_ = data["header"].copy()
    results = db_.apply(lambda row: do_date_check(date=row["report_timestamp"]), axis=1)
    expected = pd.Series([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # first entry is null
    pd.testing.assert_series_equal(results, expected)


def test_do_time_check():
    db_ = data["header"].copy()
    results = db_.apply(
        lambda row: do_time_check(hour=row["report_timestamp"].hour), axis=1
    )
    expected = pd.Series([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])  # first entry is null
    pd.testing.assert_series_equal(results, expected)


def test_do_blacklist():
    raise NotImplementedError


def test_do_day_check():
    db_ = data["header"].copy()
    results = db_.apply(
        lambda row: do_day_check(
            date=row["report_timestamp"],
            latitude=row["latitude"],
            longitude=row["longitude"],
        ),
        axis=1,
    )
    expected = pd.Series([1] * 13)  # observations are at night
    pd.testing.assert_series_equal(results, expected)


def test_humidity_blacklist():
    raise NotImplementedError


def test_mat_blacklist():
    raise NotImplementedError


def test_wind_blcklist():
    raise NotImplementedError


def test_do_air_temperature_missing_value_check():
    db_ = data["observations-at"].copy()
    results = db_.apply(
        lambda row: do_air_temperature_missing_value_check(at=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_air_temperature_anomaly_check():
    db_ = data["observations-at"].copy()
    db_.data["climatology"] = [
        277,
        278,
        279,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
    ]
    results = db_.apply(
        lambda row: do_air_temperature_anomaly_check(
            at=row["observation_value"],
            at_climatology=row["climatology"],
            maximum_anomaly=1.0,
        ),
        axis=1,
    )
    expected = pd.Series([0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_air_temperature_no_normal_check():
    db_ = data["observations-at"].copy()
    results = db_.apply(
        lambda row: do_air_temperature_no_normal_check(
            at_climatology=row["observation_value"]
        ),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_air_temperature_hard_limit_check():
    db_ = data["observations-at"].copy()
    results = db_.apply(
        lambda row: do_air_temperature_hard_limit_check(
            at=row["observation_value"],
            hard_limits=[278, 281],
        ),
        axis=1,
    )
    expected = pd.Series([1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_air_temperature_climatology_plus_stdev_check():
    db_ = data["observations-at"].copy()
    db_.data["climatology"] = [
        277,
        278,
        279,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
        280,
    ]
    results = db_.apply(
        lambda row: do_air_temperature_climatology_plus_stdev_check(
            at=row["observation_value"],
            at_climatology=row["climatology"],
            at_stdev=1.0,
            minmax_standard_deviation=[1.0, 4.0],
            maximum_standardised_anomaly=2.0,
        ),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_dpt_climatology_plus_stdev_check():
    db_ = data["observations-dpt"].copy()
    db_.data["climatology"] = [
        268,
        269,
        270,
        273,
        275,
        275,
        275,
        275,
        275,
        275,
        275,
        275,
        275,
    ]
    results = db_.apply(
        lambda row: do_air_temperature_climatology_plus_stdev_check(
            at=row["observation_value"],
            at_climatology=row["climatology"],
            at_stdev=1.0,
            minmax_standard_deviation=[1.0, 4.0],
            maximum_standardised_anomaly=2.0,
        ),
        axis=1,
    )
    expected = pd.Series([1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_dpt_missing_value_check():
    db_ = data["observations-dpt"].copy()
    results = db_.apply(
        lambda row: do_dpt_missing_value_check(dpt=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_dpt_no_normal_check():
    db_ = data["observations-dpt"].copy()
    results = db_.apply(
        lambda row: do_dpt_no_normal_check(dpt_climatology=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_supersaturation_check():
    db_ = data["observations-at"].copy()
    db2_ = data["observations-dpt"].copy()
    db_.data["observation_value_dpt"] = db2_["observation_value"]

    results = db_.apply(
        lambda row: do_supersaturation_check(
            dpt=row["observation_value_dpt"],
            at2=row["observation_value"],
        ),
        axis=1,
    )
    expected = pd.Series([1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_sst_missing_value_check():
    db_ = data["observations-sst"].copy()
    results = db_.apply(
        lambda row: do_sst_missing_value_check(sst=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    pd.testing.assert_series_equal(results, expected)


def test_do_sst_freeze_check():
    db_ = data["observations-sst"].copy()
    results = db_.apply(
        lambda row: do_sst_freeze_check(
            sst=row["observation_value"],
            freezing_point=271.35,
            freeze_check_n_sigma=2.0,
        ),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    pd.testing.assert_series_equal(results, expected)


def test_do_sst_anomaly_check():
    db_ = data["observations-sst"].copy()
    results = db_.apply(
        lambda row: do_air_temperature_anomaly_check(
            at=row["observation_value"], at_climatology=277, maximum_anomaly=1.0
        ),
        axis=1,
    )
    expected = pd.Series([0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    pd.testing.assert_series_equal(results, expected)


def test_do_sst_no_normal_check():
    db_ = data["observations-sst"].copy()
    results = db_.apply(
        lambda row: do_dpt_no_normal_check(dpt_climatology=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    pd.testing.assert_series_equal(results, expected)


def test_do_wind_missing_value_check():
    db_ = data["observations-ws"].copy()
    results = db_.apply(
        lambda row: do_wind_missing_value_check(wind_speed=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_wind_hard_limit_check():
    db_ = data["observations-ws"].copy()
    results = db_.apply(
        lambda row: do_wind_hard_limit_check(
            wind_speed=row["observation_value"],
            hard_limits=[0, 13],
        ),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def test_do_wind_consistency_check():
    db_ = data["observations-ws"].copy()
    db2_ = data["observations-wd"].copy()
    db_.data["observation_value_wd"] = db2_["observation_value"]
    results = db_.apply(
        lambda row: do_wind_consistency_check(
            wind_speed=row["observation_value"],
            wind_direction=row["observation_value_wd"],
            variable_limit=5.0,
        ),
        axis=1,
    )
    expected = pd.Series([0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    pd.testing.assert_series_equal(results, expected)


def _test_header_all():
    db_header = read_tables(cache_dir, cdm_tables="header")
    db_header["report_quality"] = db_header.apply(
        lambda row: perform_base_qc(
            pt=row["platform_type"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            timestamp=row["report_timestamp"],
            parameters={},
        ),
        axis=1,
    )

    # Do some assertion


def _test_at_all():
    db_header = read_tables(cache_dir, cdm_tables="observations-at")
    db_header["quality_flag"] = db_header.apply(
        lambda row: perform_obs_qc(at=row["observation_value"], parameters={}), axis=1
    )

    # Do some assertion


def _test_dpt_all():
    db_header = read_tables(cache_dir, cdm_tables="observations-dpt")
    db_header["quality_flag"] = db_header.apply(
        lambda row: perform_obs_qc(dpt=row["observation_value"], parameters={}), axis=1
    )

    # Do some assertion


def _test_slp_all():
    db_header = read_tables(cache_dir, cdm_tables="observations-slp")
    db_header["quality_flag"] = db_header.apply(
        lambda row: perform_obs_qc(slp=row["observation_value"], parameters={}), axis=1
    )

    # Do some assertion


def _test_sst_all():
    db_header = read_tables(cache_dir, cdm_tables="observations-sst")
    db_header["quality_flag"] = db_header.apply(
        lambda row: perform_obs_qc(sst=row["observation_value"], parameters={}), axis=1
    )

    # Do some assertion


def _test_wbt_all():
    db_header = read_tables(cache_dir, cdm_tables="observations-wbt")
    db_header["quality_flag"] = db_header.apply(
        lambda row: perform_obs_qc(wbt=row["observation_value"], parameters={}), axis=1
    )

    # Do some assertion


def _test_wd_all():
    db_header = read_tables(cache_dir, cdm_tables="observations-wd")
    db_header["quality_flag"] = db_header.apply(
        lambda row: perform_obs_qc(wd=row["observation_value"], parameters={}), axis=1
    )

    # Do some assertion


def _test_ws_all():
    db_header = read_tables(cache_dir, cdm_tables="observations-ws")
    db_header["quality_flag"] = db_header.apply(
        lambda row: perform_obs_qc(ws=row["observation_value"], parameters={}), axis=1
    )

    # Do some assertion
