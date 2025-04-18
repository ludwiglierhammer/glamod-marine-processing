from __future__ import annotations

import numpy as np

import _load_data
import pytest
from _settings import get_settings
from cdm_reader_mapper import read_tables
from cdm_reader_mapper.common.getting_files import load_file

from glamod_marine_processing.qc_suite.modules.next_level_qc import (
#    do_base_dpt_qc,
#    do_base_mat_qc,
    do_base_sst_qc,
    do_base_wind_qc,
    do_blacklist,
    do_date_check,
    do_day_check,
    do_kate_mat_qc,
    do_position_check,
    do_time_check,
    humidity_blacklist,
    is_buoy,
    is_deck_780,
    is_ship,
    mat_blacklist,
    wind_blacklist,
    do_air_temperature_missing_value_check,
    do_air_temperature_anomaly_check,
    do_air_temperature_no_normal_check,
    do_air_temperature_hard_limit_check,
    do_dpt_climatology_plus_stdev_check,
    do_supersaturation_check,
    do_dpt_missing_value_check,
    do_dpt_no_normal_check
)


def test_is_buoy():
    # For all platform types in ICOADS, flag set to 1 only if platform type corresponds to drifting buoy or
    # drifting buoy
    for pt in range(0, 47):
        result = is_buoy(pt)
        if pt in [6,7]:
            assert result == 1
        else:
            assert result == 0

def test_is_ship():
    # For all platform types in ICOADS, flag set to 1 only if platform type corresponds to drifting buoy or
    # drifting buoy
    for pt in range(0, 47):
       result = is_ship(pt)
       if pt in [0, 1, 2, 3, 4, 5, 10, 11, 12, 17]:
           assert result == 1
       else:
           assert result == 0


def test_is_deck_780():
    result = is_deck_780(780)
    assert result == 1

@pytest.mark.parametrize(
    "latitude, longitude, expected",
    [
        [0.0, 0.0, 0],
        [91.0, 0.0, 1],
        [-91.0, 0.0, 1],
        [0.0, -180.1, 1],
        [0.0, 360.1, 1]
    ]
)
def test_do_position_check(latitude, longitude, expected):
    result = do_position_check(latitude, longitude)
    assert result == expected

    # Make sure that an exception is raised if latitude or longitude is missing
    with pytest.raises(ValueError):
        result = do_position_check(None, 0.0)
    with pytest.raises(ValueError):
        result = do_position_check(0.0, None)

@pytest.mark.parametrize(
    "year, month, day, expected",
    [
        (2023, 1, 1, 0),  # 1st January 2023 PASS
        (2023, 2, 29, 1),  # 29th February 2023 FAIL
        (2023, 1, 31, 0),  # 31st January 2023 PASS
        (0, 0, 0, 1),  # 0th of 0 0 FAIL
        (2024, 2, 29, 0),  # 29th February 2024 PASS
        (2000, 2, 29, 0),  # 29th February 2000 PASS
        (1900, 2, 29, 1),  # 29th February 1900 FAIL
        (1899, 3, None, 1)  # Missing day FAIL
    ]
)
def test_do_date_check(year, month, day, expected):
    result = do_date_check(year, month, day)
    assert result == expected

   # Make sure that an exception is raised if year or month is set to None
    with pytest.raises(ValueError):
        result = do_date_check(None, 1,1)
    with pytest.raises(ValueError):
        result = do_date_check(1850, None, 1)

@pytest.mark.parametrize(
    "hour, expected",
    [
        (-1.0, 1),  # no negative hours
        (0.0, 0),
        (23.99, 0),
        (24.0, 1),  # 24 hours not allowed
        (29.2, 1),  # nothing over 24 either
        (6.34451, 0)  # check floats
    ]
)
def test_do_time_check(hour, expected):
    result = do_time_check(hour)
    assert result == expected


@pytest.mark.parametrize(
    "id, deck, year, month, latitude, longitude, platform_type, expected",
    [
        ('', 980, 1850, 1, 0, 0, 1, 1),  # fails lat/lon = 0 zero check
        ('', 874, 1850, 1, 0, 1, 1, 1),  # Deck 874 SEAS fail
        ('', 732, 1850, 1, 0, 1, 13, 1),  # C-MAN station fail
        ('', 732, 1850, 1, 0, 1, 1, 0),  # Deck 732 pass
        ('', 732, 1958, 1, 45, -172, 1, 1),  # Deck 732 fail
        ('', 732, 1974, 1, -47, -60, 1, 1),  # Deck 732 fail
        ('', 732, 1958, 1, 45, -172 + 360, 1, 1),  # Deck 732 with shifted longitude fail
        ('', 732, 1974, 1, -47, -60 + 360, 1, 1),  # Deck 732 with shifted longitude fail
        ('', 731, 1958, 1, 45, -172, 1, 0),  # Same are but not in Deck 732 should pass
        ('', 731, 1974, 1, -47, -60, 1, 0),  # Same are but not in Deck 732 should pass
        ('', 732, 1957, 1, 45, -172, 1, 0),  # Same area but wrong year should pass
        ('', 732, 1975, 1, -47, -60, 1, 0),  # Same area but wrong year should pass
    ]
)
def test_do_blacklist(id, deck, year, month, latitude, longitude, platform_type, expected):
    result = do_blacklist(id, deck, year, month, latitude, longitude, platform_type)
    assert result == expected

@pytest.mark.parametrize(
    "year, month, day, hour, latitude, longitude, time, expected",
    [
        (2015, 10, 15, 7.8000, 50.7365, -3.5344, 1.0, 1),  # Known values from direct observation
        (2018, 9, 25, 11.5000, 50.7365, -3.5344, 1.0, 1),  # Known values from direct observation
        (2015, 10, 15, 7.5000, 50.7365, -3.5344, 1.0, 0),  # Known values from direct observation
        (2025, 4, 17, 16.04, 49.160383, 5.383146, 1.0, 1),  # Known values from direct observation
        (2015, 0, 15, 7.5000, 50.7365, -3.5344, 1.0, 1),  # bad month value should trigger fail
        (2015, 10, 0, 7.5000, 50.7365, -3.5344, 1.0, 1),  # bad day value should trigger fail
        (2015, 10, 15, -7.5000, 50.7365, -3.5344, 1.0, 1)  # bad hour value should trigger fail
    ]
)
def test_do_day_check(year, month, day, hour, latitude, longitude, time, expected):
    result = do_day_check(year, month, day, hour, latitude, longitude, time)
    assert result == expected



def test_humidity_blacklist():

    for platform_type in range(0,47):
        result = humidity_blacklist(platform_type)
        if platform_type in [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 15]:
            assert result == 0
        else:
            assert result == 1

@pytest.mark.parametrize(
    "platform_type, deck, latitude, longitude, year, expected",
    [
        (5, 780, 0.5, 2.0, 2011, 1),  # Check Deck 780 platform type 5 combination that fails
        (5, 781, 0.5, 2.0, 2011, 0),  # and variants that should pass
        (6, 780, 0.5, 2.0, 2011, 0),  # and variants that should pass
        (1, 193, 45.0, -40.0, 1885, 1),  # In the exclusion zone
        (1, 193, 25.0, -40.0, 1885, 0),  # Outside the exclusion zone (in space)
        (1, 193, 45.0, -40.0, 1877, 0),  # Outside the exclusion zone (in time)
        (1, 193, 45.0, -40.0, 1999, 0),  # Outside the exclusion zone (in time)
    ]
)
def test_mat_blacklist(platform_type, deck, latitude, longitude, year, expected):
    result = mat_blacklist(platform_type, deck, latitude, longitude, year)
    assert result == expected


def test_wind_blacklist():
    for deck in range(1,1000):
        result = wind_blacklist(deck)
        if deck in [708, 780]:
            assert result == 1
        else:
            assert result == 0

@pytest.mark.parametrize(
    "at, expected",
    [
        (5.6,0),
        (None, 1),
        (np.nan, 0)
    ]
)
def test_do_air_temperature_missing_value_check(at, expected):
    assert do_air_temperature_missing_value_check(at) == expected

@pytest.mark.parametrize(
    "at, at_climatology, parameters, expected",
    [
        (5.6, 2.2, {'maximum_anomaly': 10.0}, 0),
        (None, 2.2, {'maximum_anomaly': 10.0}, 1),
        (np.nan, 2.2, {'maximum_anomaly': 10.0}, 0)
    ]
)
def test_do_air_temperature_anomaly_check(at, at_climatology, parameters, expected):
    assert do_air_temperature_anomaly_check(at, at_climatology, parameters) == expected

    with pytest.raises(KeyError):
        result = do_air_temperature_anomaly_check(5.6, 2.2, {'bad_parameter_name': 10.0})

@pytest.mark.parametrize(
    "at_climatology, expected",
    [
        (5.5, 0),
        (None, 1),
        (np.nan, 0)
    ]
)
def test_do_air_temperature_no_normal_check(at_climatology, expected):
    assert do_air_temperature_no_normal_check(at_climatology) == expected


@pytest.mark.parametrize(
    "at, parameters, expected",
    [
        (5.6, {'hard_limits': [-10.0, 10.0]}, 0),
        (15.6, {'hard_limits': [-10.0, 10.0]}, 1),
        (None, {'hard_limits': [-10.0, 10.0]}, 1),
        (np.nan, {'hard_limits': [-10.0, 10.0]}, 1)
    ]
)
def test_do_air_temperature_hard_limit_check(at, parameters, expected):
    assert do_air_temperature_hard_limit_check(at, parameters) == expected

    with pytest.raises(KeyError):
        _ = do_air_temperature_hard_limit_check(5.6, {'bad_parameter_name': [-10.0, 10.0]})


# def test_do_base_mat_qc():
#     result = do_base_mat_qc(inputs)
#     assert result == expected_value


@pytest.mark.parametrize(
    "dpt, expected",
    [
        (5.6,0),
        (None, 1),
        (np.nan, 0)
    ]
)
def test_do_dpt_missing_value_check(dpt, expected):
    assert do_dpt_missing_value_check(dpt) == expected

@pytest.mark.parametrize(
    "dpt, dpt_climatology, dpt_stdev, parameters, expected",
    [
        (5.6, 2.2, 3.3, {'minmax_standard_deviation': [1.0, 10.0], 'maximum_standardised_anomaly': 2.0}, 0),
        (15.6, 0.6, 5.0, {'minmax_standard_deviation': [1.0, 10.0], 'maximum_standardised_anomaly': 2.0}, 1),
        (1.0, 0.0, 0.1, {'minmax_standard_deviation': [1.0, 10.0], 'maximum_standardised_anomaly': 2.0}, 0),
        (15.0, 0.0, 25.0, {'minmax_standard_deviation': [1.0, 4.0], 'maximum_standardised_anomaly': 2.0}, 1),
        (None, 2.2, 3.3, {'minmax_standard_deviation': [1.0, 10.0], 'maximum_standardised_anomaly': 2.0}, 1),
        (np.nan, 2.2, 3.3, {'minmax_standard_deviation': [1.0, 10.0], 'maximum_standardised_anomaly': 2.0}, 0)
    ]
)
def test_do_dpt_climatology_plus_stdev_check(dpt, dpt_climatology, dpt_stdev, parameters, expected):
    assert do_dpt_climatology_plus_stdev_check(dpt, dpt_climatology, dpt_stdev, parameters) == expected

    test_parameters = {'minmax_standard_deviation': [1.0, 10.0], 'bad_parameter_name': 2.0}
    with pytest.raises(KeyError):
        result = do_dpt_climatology_plus_stdev_check(5.6, 2.2, 3.3, test_parameters)

    test_parameters = {'bad_parameter_name': [1.0, 10.0], 'maximum_standardised_anomaly': 2.0}
    with pytest.raises(KeyError):
        result = do_dpt_climatology_plus_stdev_check(5.6, 2.2, 3.3, test_parameters)

@pytest.mark.parametrize(
    "dpt_climatology, expected",
    [
        (5.5, 0),
        (None, 1),
        (np.nan, 0)
    ]
)
def test_do_dpt_temperature_no_normal_check(dpt_climatology, expected):
    assert do_dpt_no_normal_check(dpt_climatology) == expected


@pytest.mark.parametrize(
    "dpt, at, expected",
    [
        (3.6, 5.6, 0),  # clearly unsaturated
        (5.6, 5.6, 0),  # 100% saturation
        (15.6, 13.6, 1), # clearly supersaturated
        (None, 12.0, 1), # missing dpt FAIL
        (12.0, None, 1) # missing at FAIL
    ]
)
def test_do_supersaturation_check(dpt,at, expected):
    assert do_supersaturation_check(dpt, at) == expected



# def test_do_base_dpt_qc():
#     result = do_base_dpt_qc(inputs)
#     assert result == expected_value


def test_do_base_sst_qc():
    result = do_base_sst_qc(inputs)
    assert result == expected_value


def test_do_base_wind_qc():
    result = do_base_mat_qc(inputs)
    assert result == expected_value


def test_do_kate_mat_qc():
    result = do_base_mat_qc(inputs)
    assert result == expected_value
