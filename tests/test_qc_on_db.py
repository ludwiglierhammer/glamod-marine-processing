from __future__ import annotations

import pandas as pd
import pytest  # noqa
from _settings import get_settings
from cdm_reader_mapper import read_tables
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
    do_wind_hard_limits_check,
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
data = {}
for table in [
    "header",
    "observations-at",
    "observations-dpt",
    "observations-slp",
    "observations-sst",
    "observations-wbt",
    "observations-wd",
    "observations-ws",
]:
    load_file(
        f"{_settings.input_dir}/cdm_tables/{table}-{_settings.cdm}.psv",
        cache_dir=cache_dir,
        within_drs=False,
    )
    data[table] = read_tables(cache_dir, cdm_tables=table)


def test_is_buoy():
    db_ = data["header"].copy()
    db_ = db_["header"]
    db_["platfrom_type"] = db_["platform_type"].astype(int)
    results = db_.apply(lambda row: is_buoy(platform_type=row["platform_type"]), axis=1)
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_is_drifter():
    db_ = data["header"].copy()
    db_ = db_["header"]
    db_["platfrom_type"] = db_["platform_type"].astype(int)
    results = db_.apply(
        lambda row: is_drifter(platform_type=row["platform_type"]), axis=1
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_is_ship():
    db_ = data["header"].copy()
    db_ = db_["header"]
    results = db_.apply(lambda row: is_ship(platform_type=row["platform_type"]), axis=1)
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def _test_is_deck_780():
    db_ = data["header"].copy()
    db_ = db_["header"]
    db_["platfrom_type"] = db_["platform_type"].astype(int)
    # We have no deck in CDM
    raise NotImplementedError
    result = db_.apply(
        lambda row: is_deck_780(platform_type=row["platform_type"]), axis=1
    )


def test_do_position_check():
    db_ = data["header"].copy()
    db_ = db_["header"]
    db_["latitude"] = db_["latitude"].astype(float)
    db_["longitude"] = db_["longitude"].astype(float)
    results = db_.apply(
        lambda row: do_position_check(
            latitude=row["latitude"], longitude=row["longitude"]
        ),
        axis=1,
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_date_check():
    db_ = data["header"].copy()
    db_ = db_["header"]
    db_["report_timestamp"] = pd.to_datetime(
        db_["report_timestamp"], format="%Y-$m-$d $H:$M:$S", errors="ignore"
    )
    results = db_.apply(lambda row: do_date_check(date=row["report_timestamp"]), axis=1)
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_time_check():
    db_ = data["header"].copy()
    db_ = db_["header"]
    db_["report_timestamp"] = pd.to_datetime(
        db_["report_timestamp"], format="%Y-$m-$d $H:$M:$S", errors="ignore"
    )
    results = db_.apply(
        lambda row: do_date_check(hour=row["report_timestamp"].hour), axis=1
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_blacklist():
    raise NotImplementedError


def test_do_day_check():
    db_ = data["header"].copy()
    db_ = db_["header"]
    db_["report_timestamp"] = pd.to_datetime(
        db_["report_timestamp"], format="%Y-$m-$d $H:$M:$S", errors="ignore"
    )
    db_["latitude"] = db_["latitude"].astype(float)
    db_["longitude"] = db_["longitude"].astype(float)
    results = db_.apply(
        lambda row: do_date_check(
            year=row["report_timestamp"].year,
            month=row["report_timestamp"].month,
            day=row["report_timestamp"].day,
            hour=row["report_timestamp"].hour,
            latitude=row["latitude"],
            longitude=row["longitude"],
            time_since_sun_above_horizon=1.0,
        ),
        axis=1,
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_humidity_blacklist():
    raise NotImplementedError


def test_mat_blacklist():
    raise NotImplementedError


def test_wind_blcklist():
    raise NotImplementedError


def test_do_air_temperature_missing_value_check():
    db_ = data["observations-at"].copy()
    db_ = db_["observations-at"]
    db_["observation_value"] = db_["observation_value"].astype(float)
    results = db_.apply(
        lambda row: do_air_temperature_missing_value_check(at=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_air_temperature_anomaly_check():
    raise NotImplementedError


def test_do_air_temperature_no_normal_check():
    db_ = data["observations-at"].copy()
    db_ = db_["observations-at"]
    db_["observation_value"] = db_["observation_value"].astype(float)
    results = db_.apply(
        lambda row: do_air_temperature_missing_value_check(
            at_climatology=row["observation_value"]
        ),
        axis=1,
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_air_temperature_hard_limit_check():
    raise NotImplementedError


def test_do_air_temperature_climatology_plus_stdev_check():
    raise NotImplementedError


def test_do_dpt_climatology_plus_stdev_check():
    raise NotImplementedError


def test_do_dpt_missing_value_check():
    db_ = data["observations-dpt"].copy()
    db_ = db_["observations-dpt"]
    db_["observation_value"] = db_["observation_value"].astype(float)
    results = db_.apply(
        lambda row: do_dpt_missing_value_check(dpt=row["observation_value"]), axis=1
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_dpt_no_normal_check():
    db_ = data["observations-dpt"].copy()
    db_ = db_["observations-dpt"]
    db_["observation_value"] = db_["observation_value"].astype(float)
    results = db_.apply(
        lambda row: do_dpt_missing_value_check(
            dpt_climatology=row["observation_value"]
        ),
        axis=1,
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_supersaturation_check():
    raise NotImplementedError


def test_do_sst_missing_value_check():
    db_ = data["observations-sst"].copy()
    db_ = db_["observations-sst"]
    db_["observation_value"] = db_["observation_value"].astype(float)
    results = db_.apply(
        lambda row: do_sst_missing_value_check(sst=row["observation_value"]), axis=1
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_sst_freeze_check():
    raise NotImplementedError


def test_do_sst_anomaly_check():
    raise NotImplementedError


def test_do_sst_no_normal_check():
    db_ = data["observations-sst"].copy()
    db_ = db_["observations-sst"]
    db_["observation_value"] = db_["observation_value"].astype(float)
    results = db_.apply(
        lambda row: do_sst_missing_value_check(
            sst_climatology=row["observation_value"]
        ),
        axis=1,
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_wind_missing_value_check():
    db_ = data["observations-ws"].copy()
    db_ = db_["observations-ws"]
    db_["observation_value"] = db_["observation_value"].astype(float)
    results = db_.apply(
        lambda row: do_sst_missing_value_check(wind_speed=row["observation_value"]),
        axis=1,
    )
    expected = pd.Series([0] * 13)
    pd.testing.assert_series_equal(results, expected)


def test_do_wind_hard_limits_check():
    raise NotImplementedError


def test_do_wind_consistency_check():
    raise NotImplementedError


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
