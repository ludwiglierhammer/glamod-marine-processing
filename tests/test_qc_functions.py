from __future__ import annotations

import itertools

import numpy as np
import numpy.ma as ma
import pytest

import glamod_marine_processing.qc_suite.modules.qc as qc
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
    is_in_valid_list,
    is_ship,
    mat_blacklist,
    wind_blacklist,
)


@pytest.mark.parametrize(
    "valid_list, expected_true",
    [
        [[1, 56, 831], [1, 56, 831]],
        [["1", "56", "831"], []],
        [["1", 56, 831], [56, 831]],
        [3, [3]],
        ["3", []],
    ],
)
def test_is_in_valid_list(valid_list, expected_true):
    for val in range(0, 1000):
        result = is_in_valid_list(val, valid_list)
        if val in expected_true:
            assert result == 0
        else:
            assert result == 1


def test_is_buoy():
    # For all platform types in ICOADS, flag set to 1 only if platform type corresponds to drifting buoy or
    # drifting buoy
    for pt in range(0, 47):
        result = is_buoy(pt)
        if pt in [6, 7]:
            assert result == 0
        else:
            assert result == 1


def test_is_buoy_valid_list():
    for pt in range(0, 47):
        result = is_buoy(pt, valid_list=3)
        if pt == 3:
            assert result == 0
        else:
            assert result == 1


def test_is_drifter():
    for pt in range(0, 47):
        result = is_drifter(pt)
        if pt == 7:
            assert result == 0
        else:
            assert result == 1


def test_is_drifter_valid_list():
    for pt in range(0, 47):
        result = is_drifter(pt, valid_list=[6, 8])
        if pt in [6, 8]:
            assert result == 0
        else:
            assert result == 1


def test_is_ship():
    # For all platform types in ICOADS, flag set to 1 only if platform type corresponds to drifting buoy or
    # drifting buoy
    for pt in range(0, 47):
        result = is_ship(pt)
        if pt in [0, 1, 2, 3, 4, 5, 10, 11, 12, 17]:
            assert result == 0
        else:
            assert result == 1


def test_is_ship_valid_list():
    for pt in range(0, 47):
        result = is_ship(pt, valid_list=6)
        if pt == 6:
            assert result == 0
        else:
            assert result == 1


def test_is_deck():
    for deck in range(1000):
        result = is_deck(deck)
        if deck == 780:
            assert result == 0
        else:
            assert result == 1


def test_is_deck_valid_list():
    for deck in range(1000):
        result = is_deck(deck, valid_list=[779, 781])
        if deck in [779, 781]:
            assert result == 0
        else:
            assert result == 1


@pytest.mark.parametrize(
    "latitude, longitude, expected",
    [
        [0.0, 0.0, 0],
        [91.0, 0.0, 1],
        [-91.0, 0.0, 1],
        [0.0, -180.1, 1],
        [0.0, 360.1, 1],
        [None, 0.0, 2],
        [0.0, None, 2],
    ],
)
def test_do_position_check(latitude, longitude, expected):
    result = do_position_check(latitude, longitude)
    assert result == expected


def _test_do_position_check_raises_value_error():
    # Make sure that an exception is raised if latitude or longitude is missing
    with pytest.raises(ValueError):
        _ = do_position_check(None, 0.0)
    with pytest.raises(ValueError):
        _ = do_position_check(0.0, None)


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
        (1899, 3, None, 2),  # Missing day UNTESTABLE
        (None, 1, 1, 2),  # Missing year UNTESTABLE
        (1850, None, 1, 2),  # Missing month UNTESTABLE
    ],
)
def test_do_date_check(year, month, day, expected):
    result = do_date_check(year=year, month=month, day=day)
    assert result == expected


def _test_do_date_check_raises_value_error():
    # Make sure that an exception is raised if year or month is set to None
    with pytest.raises(ValueError):
        _ = do_date_check(None, 1, 1)
    with pytest.raises(ValueError):
        _ = do_date_check(1850, None, 1)


@pytest.mark.parametrize(
    "hour, expected",
    [
        (-1.0, 1),  # no negative hours
        (0.0, 0),
        (23.99, 0),
        (24.0, 1),  # 24 hours not allowed
        (29.2, 1),  # nothing over 24 either
        (6.34451, 0),  # check floats
        (None, 1),
    ],
)
def test_do_time_check(hour, expected):
    assert do_time_check(hour) == expected


@pytest.mark.parametrize(
    "id, deck, year, month, latitude, longitude, platform_type, expected",
    [
        ("", 980, 1850, 1, 0, 0, 1, 1),  # fails lat/lon = 0 zero check
        ("", 874, 1850, 1, 0, 1, 1, 1),  # Deck 874 SEAS fail
        ("", 732, 1850, 1, 0, 1, 13, 1),  # C-MAN station fail
        ("", 732, 1850, 1, 0, 1, 1, 0),  # Deck 732 pass
        ("", 732, 1958, 1, 45, -172, 1, 1),  # Deck 732 fail
        ("", 732, 1974, 1, -47, -60, 1, 1),  # Deck 732 fail
        (
            "",
            732,
            1958,
            1,
            45,
            -172 + 360,
            1,
            1,
        ),  # Deck 732 with shifted longitude fail
        (
            "",
            732,
            1974,
            1,
            -47,
            -60 + 360,
            1,
            1,
        ),  # Deck 732 with shifted longitude fail
        ("", 731, 1958, 1, 45, -172, 1, 0),  # Same are but not in Deck 732 should pass
        ("", 731, 1974, 1, -47, -60, 1, 0),  # Same are but not in Deck 732 should pass
        ("", 732, 1957, 1, 45, -172, 1, 0),  # Same area but wrong year should pass
        ("", 732, 1975, 1, -47, -60, 1, 0),  # Same area but wrong year should pass
        ("SUPERIGORINA", 162, 1999, 2, -10, 179, 4, 1),
        ("53521    ", 162, 2005, 11, -10, 179, 4, 1),
        ("53521    ", 162, 2007, 11, -10, 179, 4, 0),
    ],
)
def test_do_blacklist(
    id, deck, year, month, latitude, longitude, platform_type, expected
):
    result = do_blacklist(id, deck, year, month, latitude, longitude, platform_type)
    assert result == expected


@pytest.mark.parametrize(
    "year, month, day, hour, latitude, longitude, time, expected",
    [
        (
            2015,
            10,
            15,
            7.8000,
            50.7365,
            -3.5344,
            1.0,
            0,
        ),  # Known values from direct observation (day); should trigger pass
        (
            2018,
            9,
            25,
            11.5000,
            50.7365,
            -3.5344,
            1.0,
            0,
        ),  # Known values from direct observation (day); should trigger pass
        (
            2015,
            10,
            15,
            7.5000,
            50.7365,
            -3.5344,
            1.0,
            1,
        ),  # Known values from direct observation (night); should trigger fail
        (
            2025,
            4,
            17,
            16.04,
            49.160383,
            5.383146,
            1.0,
            0,
        ),  # Known values from direct observation: should trigger pass
        (
            2015,
            0,
            15,
            7.5000,
            50.7365,
            -3.5344,
            1.0,
            1,
        ),  # bad month value should trigger fail
        (
            2015,
            10,
            0,
            7.5000,
            50.7365,
            -3.5344,
            1.0,
            1,
        ),  # bad day value should trigger fail
        (
            2015,
            10,
            15,
            -7.5000,
            50.7365,
            -3.5344,
            1.0,
            1,
        ),  # bad hour value should trigger fail
        (
            2015,
            1,
            1,
            0.5,
            0.0,
            0.0,
            1,
            1,
        ),  # 0 lat 0 lon near midnight should trigger fail
        (2015, 1, 1, None, 0.0, 0.0, 1, 1),  # missing hour should trigger fail
    ],
)
def test_do_day_check(year, month, day, hour, latitude, longitude, time, expected):
    result = do_day_check(
        year=year,
        month=month,
        day=day,
        hour=hour,
        latitude=latitude,
        longitude=longitude,
        time_since_sun_above_horizon=time,
    )
    assert result == expected


def test_humidity_blacklist():
    for platform_type in range(0, 47):
        result = humidity_blacklist(platform_type)
        if platform_type in [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 15]:
            assert result == 0
        else:
            assert result == 1


@pytest.mark.parametrize(
    "platform_type, deck, latitude, longitude, year, expected",
    [
        (
            5,
            780,
            0.5,
            2.0,
            2011,
            1,
        ),  # Check Deck 780 platform type 5 combination that fails
        (5, 781, 0.5, 2.0, 2011, 0),  # and variants that should pass
        (6, 780, 0.5, 2.0, 2011, 0),  # and variants that should pass
        (1, 193, 45.0, -40.0, 1885, 1),  # In the exclusion zone
        (1, 193, 25.0, -40.0, 1885, 0),  # Outside the exclusion zone (in space)
        (1, 193, 45.0, -40.0, 1877, 0),  # Outside the exclusion zone (in time)
        (1, 193, 45.0, -40.0, 1999, 0),  # Outside the exclusion zone (in time)
    ],
)
def test_mat_blacklist(platform_type, deck, latitude, longitude, year, expected):
    result = mat_blacklist(platform_type, deck, latitude, longitude, year)
    assert result == expected


def test_wind_blacklist():
    for deck in range(1, 1000):
        result = wind_blacklist(deck)
        if deck in [708, 780]:
            assert result == 1
        else:
            assert result == 0


@pytest.mark.parametrize(
    "at, expected", [(5.6, 0), (None, 1), (np.nan, 1)]
)  # not sure if np.nan should trigger FAIL
def test_do_air_temperature_missing_value_check(at, expected):
    assert do_air_temperature_missing_value_check(at) == expected


@pytest.mark.parametrize(
    "at, at_climatology, maximum_anomaly, expected",
    [
        (5.6, 2.2, 10.0, 0),
        (None, 2.2, 10.0, 1),
        (np.nan, 2.2, 10.0, 1),  # not sure if np.nan should trigger FAIL
    ],
)
def test_do_air_temperature_anomaly_check(
    at, at_climatology, maximum_anomaly, expected
):
    assert (
        do_air_temperature_anomaly_check(at, at_climatology, maximum_anomaly)
        == expected
    )


@pytest.mark.parametrize(
    "at_climatology, expected", [(5.5, 0), (None, 1), (np.nan, 1)]
)  # not sure if np.nan should trigger FAIL
def test_do_air_temperature_no_normal_check(at_climatology, expected):
    assert do_air_temperature_no_normal_check(at_climatology) == expected


@pytest.mark.parametrize(
    "at, hard_limits, expected",
    [
        (5.6, [-10.0, 10.0], 0),
        (15.6, [-10.0, 10.0], 1),
        (None, [-10.0, 10.0], 1),
        (np.nan, [-10.0, 10.0], 1),
    ],
)
def test_do_air_temperature_hard_limit_check(at, hard_limits, expected):
    assert do_air_temperature_hard_limit_check(at, hard_limits) == expected


@pytest.mark.parametrize(
    "at, at_climatology, at_stdev, minmax_standard_deviation, maximum_standardised_anomaly, expected",
    [
        (
            5.6,
            2.2,
            3.3,
            [1.0, 10.0],
            2.0,
            0,
        ),
        (
            15.6,
            0.6,
            5.0,
            [1.0, 10.0],
            2.0,
            1,
        ),
        (
            1.0,
            0.0,
            0.1,
            [1.0, 10.0],
            2.0,
            0,
        ),
        (
            15.0,
            0.0,
            25.0,
            [1.0, 4.0],
            2.0,
            1,
        ),
        (
            None,
            2.2,
            3.3,
            [1.0, 10.0],
            2.0,
            1,
        ),
        (
            np.nan,
            2.2,
            3.3,
            [1.0, 10.0],
            2.0,
            1,  # not sure if np.nan should trigger FAIL
        ),
    ],
)
def test_do_air_temperature_climatology_plus_stdev_check(
    at,
    at_climatology,
    at_stdev,
    minmax_standard_deviation,
    maximum_standardised_anomaly,
    expected,
):
    assert (
        do_air_temperature_climatology_plus_stdev_check(
            at,
            at_climatology,
            at_stdev,
            minmax_standard_deviation,
            maximum_standardised_anomaly,
        )
        == expected
    )


@pytest.mark.parametrize(
    "dpt, expected", [(5.6, 0), (None, 1), (np.nan, 1)]
)  # not sure if np.nan should trigger FAIL
def test_do_dpt_missing_value_check(dpt, expected):
    assert do_dpt_missing_value_check(dpt) == expected


@pytest.mark.parametrize(
    "dpt, dpt_climatology, dpt_stdev, minmax_standard_deviation, maximum_standardised_anomaly, expected",
    [
        (
            5.6,
            2.2,
            3.3,
            [1.0, 10.0],
            2.0,
            0,
        ),
        (
            15.6,
            0.6,
            5.0,
            [1.0, 10.0],
            2.0,
            1,
        ),
        (
            1.0,
            0.0,
            0.1,
            [1.0, 10.0],
            2.0,
            0,
        ),
        (
            15.0,
            0.0,
            25.0,
            [1.0, 4.0],
            2.0,
            1,
        ),
        (
            None,
            2.2,
            3.3,
            [1.0, 10.0],
            2.0,
            1,
        ),
        (
            np.nan,
            2.2,
            3.3,
            [1.0, 10.0],
            2.0,
            1,  # not sure if np.nan should trigger FAIL
        ),
    ],
)
def test_do_dpt_climatology_plus_stdev_check(
    dpt,
    dpt_climatology,
    dpt_stdev,
    minmax_standard_deviation,
    maximum_standardised_anomaly,
    expected,
):
    assert (
        do_dpt_climatology_plus_stdev_check(
            dpt,
            dpt_climatology,
            dpt_stdev,
            minmax_standard_deviation,
            maximum_standardised_anomaly,
        )
        == expected
    )


@pytest.mark.parametrize(
    "dpt_climatology, expected",
    [(5.5, 0), (None, 1), (np.nan, 1)],  # not sure if np.nan should trigger FAIL
)
def test_do_dpt_temperature_no_normal_check(dpt_climatology, expected):
    assert do_dpt_no_normal_check(dpt_climatology) == expected


@pytest.mark.parametrize(
    "dpt, at, expected",
    [
        (3.6, 5.6, 0),  # clearly unsaturated
        (5.6, 5.6, 0),  # 100% saturation
        (15.6, 13.6, 1),  # clearly supersaturated
        (None, 12.0, 1),  # missing dpt FAIL
        (12.0, None, 1),  # missing at FAIL
    ],
)
def test_do_supersaturation_check(dpt, at, expected):
    assert do_supersaturation_check(dpt, at) == expected


@pytest.mark.parametrize(
    "sst, expected", [(5.6, 0), (None, 1), (np.nan, 1)]
)  # not sure if np.nan should trigger FAIL
def test_do_sst_missing_value_check(sst, expected):
    assert do_sst_missing_value_check(sst) == expected


@pytest.mark.parametrize(
    "sst, sst_climatology, maximum_anomaly, expected",
    [
        (5.6, 2.2, 10.0, 0),
        (None, 2.2, 10.0, 1),
        (np.nan, 2.2, 10.0, 1),  # not sure if np.nan should trigger FAIL
    ],
)
def test_do_sst_anomaly_check(sst, sst_climatology, maximum_anomaly, expected):
    assert do_sst_anomaly_check(sst, sst_climatology, maximum_anomaly) == expected


@pytest.mark.parametrize(
    "sst_climatology, expected",
    [(5.5, 0), (None, 1), (np.nan, 1)],  # not sure if np.nan should trigger FAIL
)
def test_do_sst_no_normal_check(sst_climatology, expected):
    assert do_sst_no_normal_check(sst_climatology) == expected


@pytest.mark.parametrize(
    "sst, freezing_point, freeze_check_n_sigma, expected",
    [
        (5.6, -1.8, 2.0, 0),
        (-5.6, -1.8, 2.0, 1),
        (0.0, -1.8, 2.0, 0),
        (5.6, 11.8, 2.0, 1),
    ],
)
def test_do_sst_freeze_check(sst, freezing_point, freeze_check_n_sigma, expected):
    assert do_sst_freeze_check(sst, freezing_point, freeze_check_n_sigma) == expected


@pytest.mark.parametrize(
    "w, expected", [(5.6, 0), (None, 1), (np.nan, 1)]
)  # not sure if np.nan should trigger FAIL
def test_do_wind_missing_value_check(w, expected):
    assert do_wind_missing_value_check(w) == expected


@pytest.mark.parametrize(
    "w, parameters, expected",
    [
        (5.6, [-10.0, 10.0], 0),
        (15.6, [-10.0, 10.0], 1),
        (None, [-10.0, 10.0], 1),
        (np.nan, [-10.0, 10.0], 1),
    ],
)
def test_do_wind_hard_limit_check(w, parameters, expected):
    assert do_wind_hard_limit_check(w, parameters) == expected


@pytest.mark.parametrize(
    "wind_speed, wind_direction, variable_limit, expected",
    [
        (None, 4, 3, 1),  # missing wind speed
        (4, None, 3, 1),
        (0, 361, 3, 0),
        (5, 361, 3, 1),
        (12.0, 362, 10.0, 1),
    ],
)
def test_do_wind_consistency_check(
    wind_speed, wind_direction, variable_limit, expected
):
    assert (
        do_wind_consistency_check(wind_speed, wind_direction, variable_limit)
        == expected
    )


@pytest.mark.parametrize(
    "y1, m1, y2, m2, expected",
    [
        (2024, 1, 2024, 1, 1),
        (2023, 1, 2024, 1, 0),
        (2024, 1, 2024, 2, 0),
        (2021, 12, 2025, 3, 0),
    ],
)
def test_month_match(y1, m1, y2, m2, expected):
    assert qc.month_match(y1, m1, y2, m2) == expected


@pytest.mark.parametrize(
    "year, month, day, expected_year, expected_month, expected_day",
    [
        (2024, 1, 1, 2023, 12, 31),
        (2024, 3, 1, 2024, 2, 29),
        (2023, 3, 1, 2023, 2, 28),
        (2024, 12, 31, 2024, 12, 30),
        (2024, 2, 29, 2024, 2, 28),
        (2025, 2, 29, None, None, None),
    ],
)
def test_yesterday(year, month, day, expected_year, expected_month, expected_day):
    assert qc.yesterday(year, month, day) == (
        expected_year,
        expected_month,
        expected_day,
    )


@pytest.mark.parametrize(
    "month, expected",
    [
        (1, "DJF"),
        (2, "DJF"),
        (3, "MAM"),
        (4, "MAM"),
        (5, "MAM"),
        (6, "JJA"),
        (7, "JJA"),
        (8, "JJA"),
        (9, "SON"),
        (10, "SON"),
        (11, "SON"),
        (12, "DJF"),
        (0, None),
        (-1, None),
        (13, None),
    ],
)
def test_seasons(month, expected):
    assert qc.season(month) == expected


def test_pentad_to_mont():
    for p in range(1, 74):
        m, d = qc.pentad_to_month_day(p)
        assert p == qc.which_pentad(m, d)


@pytest.mark.parametrize(
    "month, day, expected",
    [
        (1, 6, 2),
        (1, 21, 5),
        (12, 26, 72),
        (1, 1, 1),
        (12, 31, 73),
        (2, 29, 12),
        (3, 1, 12),
    ],
)
def test_which_pentad(month, day, expected):
    assert qc.which_pentad(month, day) == expected


def test_which_pentad_raises_value_error():
    with pytest.raises(ValueError):
        qc.which_pentad(13, 1)
    with pytest.raises(ValueError):
        qc.which_pentad(1, 41)


def test_day_in_year_leap_year():
    assert qc.day_in_year(2, 29) == qc.day_in_year(3, 1)

    # Just test all days
    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    count = 1
    for month in range(1, 13):
        for day in range(1, month_lengths[month - 1] + 1):
            assert qc.day_in_year(month, day) == count
            count += 1


def test_day_in_year_leap_year_test():
    with pytest.raises(ValueError):
        qc.day_in_year(13, 1)
    with pytest.raises(ValueError):
        qc.day_in_year(0, 1)
    with pytest.raises(ValueError):
        qc.day_in_year(2, 30)
    with pytest.raises(ValueError):
        qc.day_in_year(2, 0)


@pytest.fixture
def hires_field():
    outfield = np.zeros((365, 1, 180 * 4, 360 * 4))
    outfield[:, :, -1, :] = -999
    return outfield


@pytest.mark.parametrize(
    "lat, lon, month, day, expected",
    [
        (-89.9, -179.9, 1, 1, None),
        (89.89, -179.9, 1, 1, 0),
        (89.89, -179.9 + 0.25, 1, 1, 0),
        (89.89, 179.9, 1, 1, 0),
    ],
)
def test_get_hires_sst(lat, lon, month, day, expected, hires_field):
    assert qc.get_hires_sst(lat, lon, month, day, hires_field) == expected


@pytest.fixture
def midres_field_masked():
    outfield = np.zeros((365, 180, 360)) + 5.1
    outfield = outfield.view(ma.MaskedArray)
    outfield[:, 179, :] = ma.masked  # Emulate Antarctica having missing data
    return outfield


@pytest.mark.parametrize(
    "lat, lon, month, day, expected",
    [
        (-89.9, -179.9, 1, 1, None),
        (89.89, -179.9, 1, 1, 5.1),
        (89.89, 179.9, 1, 1, 5.1),
    ],
)
def test_get_sst_daily(lat, lon, month, day, expected, midres_field_masked):
    assert qc.get_sst_daily(lat, lon, month, day, midres_field_masked) == expected


@pytest.fixture
def pentad_field():
    """Construct a 1x1xpentad grid with entries equal to pentad + latitude/100."""
    outfield = np.zeros((73, 180, 360))
    for pp, yy in itertools.product(range(73), range(180)):
        outfield[pp, yy, :] = pp + (89.5 - yy) / 100.0
    return outfield


@pytest.fixture
def single_field():
    """Construct a 1x1xpentad grid with entries equal to pentad + latitude/100."""
    outfield = np.zeros((1, 180, 360))
    for pp, yy in itertools.product(range(1), range(180)):
        outfield[pp, yy, :] = pp + (89.5 - yy) / 100.0
    return outfield


@pytest.mark.parametrize(
    "lat, lon, month, day, expected",
    [
        (89.9, 0.0, 12, 31, 72 + 0.895),
        (89.9, 0.0, 1, 1, 0 + 0.895),
        (-9.5, -179.5, 1, 1, 0 - 0.095),
        (-10.5, -179.5, 12, 31, 72 - 0.105),
        (89.9, 0.0, 1, 1, 0 + 0.895),
        (89.9, 0.0, 1, 1, 0 + 0.895),
        (0.5, -179.5, 1, 1, 0 + 0.005),
        (-0.5, -179.5, 1, 1, 0 - 0.005),
        (0.5, -179.5, 1, 1, 0 + 0.005),
        (-0.5, -179.5, 1, 1, 0 - 0.005),
        (-89.9, 0.0, 1, 1, 0 - 0.895),
        (0, 0, 1, 1, 0 - 0.005),
    ],
)
def test_get_sst(lat, lon, month, day, expected, pentad_field):
    assert qc.get_sst(lat, lon, month, day, pentad_field) == expected


@pytest.mark.parametrize(
    "lat, lon, month, day, expected",
    [
        (89.9, 0.0, 12, 31, 0 + 0.895),
        (89.9, 0.0, 1, 1, 0 + 0.895),
        (-9.5, -179.5, 1, 1, 0 - 0.095),
        (-10.5, -179.5, 12, 31, 0 - 0.105),
        (89.9, 0.0, 1, 1, 0 + 0.895),
        (89.9, 0.0, 1, 1, 0 + 0.895),
        (0.5, -179.5, 1, 1, 0 + 0.005),
        (-0.5, -179.5, 1, 1, 0 - 0.005),
        (0.5, -179.5, 1, 1, 0 + 0.005),
        (-0.5, -179.5, 1, 1, 0 - 0.005),
        (-89.9, 0.0, 1, 1, 0 - 0.895),
        (0, 0, 1, 1, 0 - 0.005),
    ],
)
def test_get_sst_with_single_field(lat, lon, month, day, expected, single_field):
    assert qc.get_sst(lat, lon, month, day, single_field) == expected


@pytest.mark.parametrize(
    "lat, lon, expected",
    [
        (89.9, 0.0, 0 + 0.895),
        (89.9, 0.0, 0 + 0.895),
        (-9.5, -179.5, 0 - 0.095),
        (-10.5, -179.5, 0 - 0.105),
        (89.9, 0.0, 0 + 0.895),
        (89.9, 0.0, 0 + 0.895),
        (0.5, -179.5, 0 + 0.005),
        (-0.5, -179.5, 0 - 0.005),
        (0.5, -179.5, 0 + 0.005),
        (-0.5, -179.5, 0 - 0.005),
        (-89.9, 0.0, 0 - 0.895),
        (0, 0, 0 - 0.005),
    ],
)
def test_get_sst_single_field(lat, lon, expected, single_field):
    assert qc.get_sst_single_field(lat, lon, single_field) == expected


@pytest.mark.parametrize(
    "x1, x2, y1, y2, x, y, q11, q12, q21, q22, expected",
    [
        (0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),  # zero when all zero
        (
            0.0,
            1.0,
            0.0,
            1.0,
            0.5,
            0.5,
            0.0,
            1.0,
            1.0,
            2.0,
            1.0,
        ),  # test_gradient_across_square
        (0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 2.0, 0.0),
        (0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 2.0, 2.0),
        (0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 2.0, 1.0),
        (0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 2.0, 1.0),
        (
            0.0,
            1.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0,
            1.0,
            0.0,
        ),  # test_zero_at_point_set_to_zero
        (
            0.0,
            1.0,
            0.0,
            1.0,
            0.0,
            1.0,
            0.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ),  # test_one_at_points_set_to_one
        (0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0),
        (0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0),
        (
            0.0,
            1.0,
            0.0,
            1.0,
            0.5,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0,
            0.5,
        ),  # test_half_at_point_halfway_between_zero_and_one
        (0.0, 1.0, 0.0, 1.0, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 0.5),
    ],
)
def test_bilinear_interp(x1, x2, y1, y2, x, y, q11, q12, q21, q22, expected):
    assert qc.bilinear_interp(x1, x2, y1, y2, x, y, q11, q12, q21, q22) == expected


@pytest.mark.parametrize(
    "array, expected",
    [
        ([None, None], None),
        ([None, 7.3], 7.3),
        ([994.2, None], 994.2),
        ([1.0, 6.0], 3.5),
    ],
)
def test_missing_mean(array, expected):
    assert qc.missing_mean(array) == expected


@pytest.mark.parametrize(
    "q11, q12, q21, q22, expected",
    [
        (None, None, None, None, (None, None, None, None)),
        (1.0, 2.0, 3.0, None, (1.0, 2.0, 3.0, 2.5)),
        (None, 2.0, 3.0, None, (2.5, 2.0, 3.0, 2.5)),
        (None, None, 3.0, None, (3.0, 3.0, 3.0, 3.0)),
    ],
)
def test_fill_missing_values(q11, q12, q21, q22, expected):
    assert qc.fill_missing_vals(q11, q12, q21, q22) == expected


@pytest.mark.parametrize(
    "lat, lon, max90, expected",
    [
        (0.4, 322.2 - 360, 1, (-38.5, -37.5, -0.5, 0.5)),
        (89.9, 0.1, 1, (-0.5, 0.5, 89.5, 89.5)),
        (89.9, 0.1, 0, (-0.5, 0.5, 89.5, 90.5)),
        (0.1, 0.1, 1, (-0.5, 0.5, -0.5, 0.5)),
        (0.0, 0.0, 1, (-0.5, 0.5, -0.5, 0.5)),
        (0.0, 179.9, 1, (179.5, 180.5, -0.5, 0.5)),
        (0.0, -179.9, 1, (-180.5, -179.5, -0.5, 0.5)),
    ],
)
def test_get_four_surrounding_points(lat, lon, max90, expected):
    assert qc.get_four_surrounding_points(lat, lon, max90) == expected


@pytest.mark.parametrize(
    "value, climate_normal, standard_deviation, limit, lowbar, expected",
    [
        (None, 0.0, 1.0, 3.0, 0.5, 1),  # check None returns fail
        (1.0, None, 1.0, 3.0, 0.5, 1),
        (1.0, 0.0, None, 3.0, 0.5, 1),
        (1.0, 0.0, 2.0, 3.0, 0.1, 0),  # Check simple pass 1.0 anomaly with 6.0 limits
        (7.0, 0.0, 2.0, 3.0, 0.1, 1),  # Check fail with 7.0 anomaly and 6.0 limits
        (
            0.4,
            0.0,
            0.1,
            3.0,
            0.5,
            0,
        ),  # check lowbar works anomaly outside std limits but less than lowbar
    ],
)
def test_climatology_plus_stdev_with_lowbar(
    value, climate_normal, standard_deviation, limit, lowbar, expected
):
    assert (
        qc.climatology_plus_stdev_with_lowbar(
            value, climate_normal, standard_deviation, limit, lowbar
        )
        == expected
    )


@pytest.mark.parametrize(
    "value, climate_normal, standard_deviation, stdev_limits, limit, expected",
    [
        (None, 0.0, 0.5, [0.0, 1.0], 5.0, 1),  # fails with None
        (2.0, None, 0.5, [0.0, 1.0], 5.0, 1),  # fails with None
        (2.0, 0.0, None, [0.0, 1.0], 5.0, 1),  # fails with None
        (2.0, 0.0, 0.5, [0.0, 1.0], 5.0, 0),  # simple pass
        (2.0, 0.0, 0.5, [0.0, 1.0], 3.0, 1),  # simple fail
        (3.0, 0.0, 1.5, [0.0, 1.0], 2.0, 1),  # fail with limited stdev
        (1.0, 0.0, 0.1, [0.5, 1.0], 5.0, 0),  # pass with limited stdev
        (1.0, 0.0, 0.5, [1.0, 0.0], 5.0, 2),  # untestable with limited stdev
        (1.0, 0.0, 0.5, [0.0, 1.0], -1, 2),  # untestable with limited stdev
    ],
)
def test_climatology_plus_stdev_check(
    value, climate_normal, standard_deviation, stdev_limits, limit, expected
):
    assert (
        qc.climatology_plus_stdev_check(
            value, climate_normal, standard_deviation, stdev_limits, limit
        )
        == expected
    )


def _test_climatology_plus_stdev_check_raises():
    with pytest.raises(ValueError):
        qc.climatology_plus_stdev_check(1.0, 0.0, 0.5, [1.0, 0.0], 5.0)
    with pytest.raises(ValueError):
        qc.climatology_plus_stdev_check(1.0, 0.0, 0.5, [0.0, 1.0], -1)


@pytest.mark.parametrize(
    "value, climate_normal, limit, expected",
    [
        (8.0, 0.0, 8.0, 0),  # pass at limit
        (9.0, 0.0, 8.0, 1),  # fail with anomaly exceeding limit
        (0.0, 9.0, 8.0, 1),  # fail with same anomaly but negative
        (9.0, 0.0, 11.0, 0),  # pass with higher limit
        (0.0, 9.0, 11.0, 0),  # same with negative anomaly
        (None, 0.0, 8.0, 1),  # Fail with Nones as inputs
        (9.0, None, 8.0, 1),  # Fail with Nones as inputs
        (9.0, 0.0, None, 1),  # Fail with Nones as inputs
    ],
)
def test_climatology_check(value, climate_normal, limit, expected):
    assert qc.climatology_check(value, climate_normal, limit) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, 1),
        (5.7, 0),
    ],
)
def test_value_check(value, expected):
    assert qc.value_check(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, 1),
        (5.7, 0),
    ],
)
def test_no_normal_check(value, expected):
    assert qc.no_normal_check(value) == expected


@pytest.mark.parametrize(
    "value, limits, expected",
    [
        (5.0, [-20.0, 20.0], 0),
        (25.0, [-20.0, 20.0], 1),
        (-10.0, [-30, 15.0], 0),
    ],
)
def test_hard_limit(value, limits, expected):
    assert qc.hard_limit(value, limits) == expected


@pytest.mark.parametrize(
    "sst, sst_uncertainty, freezing_point, n_sigma, expected",
    [
        (15.0, 0.0, -1.8, 2.0, 0),
        (-15.0, 0.0, -1.8, 2.0, 1),
        (-2.0, 0.0, -2.0, 2.0, 0),
        (-2.0, 0.5, -1.8, 2.0, 0),
        (-5.0, 0.5, -1.8, 2.0, 1),
        (0.0, None, -1.8, 2.0, 2),
        (0.0, 0.0, None, 2.0, 2),
    ],
)
def test_sst_freeze_check(sst, sst_uncertainty, freezing_point, n_sigma, expected):
    assert (
        qc.sst_freeze_check(sst, sst_uncertainty, freezing_point, n_sigma) == expected
    )


def _test_sst_freeze_check_raises():
    with pytest.raises(ValueError):
        qc.sst_freeze_check(0.0, None, -1.8, 2.0)
    with pytest.raises(ValueError):
        qc.sst_freeze_check(0.0, 0.0, None, 2.0)


def test_sst_freeze_check_defaults():
    assert qc.sst_freeze_check(0.0) == 0
    assert qc.sst_freeze_check(-1.8) == 0
    assert qc.sst_freeze_check(-2.0) == 1


@pytest.mark.parametrize(
    "angle1, angle2, expected",
    [(0.0, 1.0, 1.0), (0.0, 3 * np.pi / 2, np.pi / 2), (0, 2 * np.pi, 0)],
)
def test_angle_diff(angle1, angle2, expected):
    assert qc.angle_diff(angle1, angle2) == expected


def test_angle_diff_raises():
    with pytest.raises(ValueError):
        qc.angle_diff(None, 1.0)
    with pytest.raises(ValueError):
        qc.angle_diff(1.0, None)
