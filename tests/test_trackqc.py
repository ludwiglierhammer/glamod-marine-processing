from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import glamod_marine_processing.qc_suite.modules.Extended_IMMA as ex

# import glamod_marine_processing.qc_suite.modules.next_level_trackqc as tqc
import glamod_marine_processing.qc_suite.modules.trackqc as otqc
from glamod_marine_processing.qc_suite.modules.IMMA1 import IMMA
from glamod_marine_processing.qc_suite.modules.next_level_track_check_qc import (
    calculate_speed_course_distance_time_difference,
)


def test_daytime_exeter():
    daytime = otqc.track_day_test(2019, 6, 21, 12.0, 50.7, -3.5, elevdlim=-2.5)
    assert daytime


def test_nighttime_exeter():
    daytime = otqc.track_day_test(2019, 6, 21, 0.0, 50.7, -3.5, elevdlim=-2.5)
    assert not (daytime)


def test_large_elevdlim_exeter():
    daytime = otqc.track_day_test(2019, 6, 21, 12.0, 50.7, -3.5, elevdlim=89.0)
    assert not (daytime)


def test_lat_is_zero():
    assert otqc.track_day_test(2022, 5, 3, 12.0, 0.0, 0.0, elevdlim=-2.5)


@pytest.mark.parametrize(
    "year, month, day, hour, lat, lon",
    [
        (2019, 13, 21, 0.0, 50.7, -3.5),
        (None, 12, 21, 0.0, 50.7, -3.5),
        (2019, None, 21, 0.0, 50.7, -3.5),
        (2019, 12, None, 0.0, 50.7, -3.5),
        (2019, 12, 21, None, 50.7, -3.5),
        (2019, 12, 21, 0.0, None, -3.5),
        (2019, 12, 21, 0.0, 50.7, None),
        (2019, 12, 43, 0.0, 50.7, -3.5),
        (2019, 12, 21, -5.0, 50.7, -3.5),
        (2019, 12, 21, 0.0, -99.0, -3.5),
    ],
)
def test_error_invalid_parameter(year, month, day, hour, lat, lon):
    with pytest.raises(ValueError):
        assert otqc.track_day_test(year, month, day, hour, lat, lon, elevdlim=-2.5)


def test_no_trim():
    arr = np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    trim = otqc.trim_mean(arr, 0)
    assert trim == 4.0
    assert np.all(
        arr == np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    )  # this checks the array is not modifed by the function


def test_with_trim():
    arr = np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    trim = otqc.trim_mean(arr, 5)
    assert trim == 3.0
    assert np.all(
        arr == np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    )  # this checks the array is not modifed by the function


def test_sd_no_trim():
    arr = np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    trim = otqc.trim_std(arr, 0)
    assert trim == 2.0
    assert np.all(
        arr == np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    )  # this checks the array is not modifed by the function


def test_sd_with_trim():
    arr = np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    trim = otqc.trim_std(arr, 5)
    assert trim == 0.0
    assert np.all(
        arr == np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    )  # this checks the array is not modifed by the function


def make_test_data(selection):
    if selection == 1:
        # stationary drifter
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 2:
        # stationary drifter (artificial 'jitter' spikes)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 1.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": 1.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 3:
        # stationary drifter (artificial 'jitter' which won't be fully smoothed and outside tolerance)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 1.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 1.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 4:
        # stationary drifter (artificial 'jitter' which won't be fully smoothed and within tolerance)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.01,
                "LON": 0.01,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.01,
                "LON": 0.01,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 5:
        # moving drifter (going west)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.02,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.04,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.06,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.08,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.10,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.12,
                "SST": 5.0,
            },
        ]
    elif selection == 6:
        # moving drifter (going north)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.02,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.04,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.06,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.08,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.10,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.12,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 7:
        # runs aground (drifter going north then stops)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.02,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.04,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.06,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.08,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.08,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.08,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 8:
        # stationary drifter (high frequency sampling prevents detection)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 1,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 2,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 3,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 4,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 5,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 6,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 7,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 9:
        # stationary drifter (low frequency sampling prevents detection)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 10,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 13,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 16,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 19,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 10:
        # stationary drifter (mid frequency sampling enables detection)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 0,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 0,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 9,
                "HR": 0,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 10,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 11:
        # stationary drifter (changed sampling prevents early detection)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 8,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 9,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 10,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 11,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 12:
        # moving drifter (going northwest at equator but going slowly and within tolerance)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.005,
                "LON": -0.005,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.01,
                "LON": -0.01,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.015,
                "LON": -0.015,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.02,
                "LON": -0.02,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.025,
                "LON": -0.025,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.03,
                "LON": -0.03,
                "SST": 5.0,
            },
        ]
    elif selection == 13:
        # moving drifter (going west in high Arctic but going slower than tolerance set at equator)
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 85.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 85.0,
                "LON": -0.02,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 85.0,
                "LON": -0.04,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 85.0,
                "LON": -0.06,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 85.0,
                "LON": -0.08,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 85.0,
                "LON": -0.10,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 85.0,
                "LON": -0.12,
                "SST": 5.0,
            },
        ]
    elif selection == 14:
        # stationary then moves
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.02,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.04,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.06,
                "LON": 0.0,
                "SST": 5.0,
            },
        ]
    elif selection == 15:
        # too short for QC
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.02,
                "SST": 5.0,
            },
        ]
    elif selection == 16:
        # assertion error - bad input parameter
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.02,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.04,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.06,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.08,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.10,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.12,
                "SST": 5.0,
            },
        ]
    elif selection == 17:
        # assertion error - missing observation
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.02,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.04,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 4,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.06,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.08,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.10,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.12,
                "SST": 5.0,
            },
        ]
    elif selection == 18:
        # assertion error - times not sorted
        vals = [
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 1,
                "HR": 12,
                "LAT": 0.0,
                "LON": 0.0,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.02,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 3,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.04,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 2,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.06,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 5,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.08,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 6,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.10,
                "SST": 5.0,
            },
            {
                "ID": "AAAAAAAAA",
                "YR": 2003,
                "MO": 12,
                "DY": 7,
                "HR": 12,
                "LAT": 0.0,
                "LON": -0.12,
                "SST": 5.0,
            },
        ]

    from datetime import datetime

    id = [x["ID"] for x in vals]
    date = [datetime(x["YR"], x["MO"], x["DY"], x["HR"]) for x in vals]
    lat = [x["LAT"] for x in vals]
    lon = [x["LON"] for x in vals]
    sst = [x["SST"] for x in vals]

    df = pd.DataFrame({"id": id, "date": date, "lat": lat, "lon": lon, "sst": sst})
    df = calculate_speed_course_distance_time_difference(df)

    return df


@pytest.fixture
def vals1():
    return make_test_data(1)


@pytest.fixture
def vals2():
    return make_test_data(2)


@pytest.fixture
def vals3():
    return make_test_data(3)


@pytest.fixture
def vals4():
    return make_test_data(4)


@pytest.fixture
def vals5():
    return make_test_data(5)


@pytest.fixture
def vals6():
    return make_test_data(6)


@pytest.fixture
def vals7():
    return make_test_data(7)


@pytest.fixture
def vals8():
    return make_test_data(8)


@pytest.fixture
def vals9():
    return make_test_data(9)


@pytest.fixture
def vals10():
    return make_test_data(10)


@pytest.fixture
def vals11():
    return make_test_data(11)


@pytest.fixture
def vals12():
    return make_test_data(12)


@pytest.fixture
def vals13():
    return make_test_data(13)


@pytest.fixture
def vals14():
    return make_test_data(14)


@pytest.fixture
def vals15():
    return make_test_data(15)


@pytest.fixture
def vals16():
    return make_test_data(16)


@pytest.fixture
def vals17():
    return make_test_data(17)


@pytest.fixture
def vals18():
    return make_test_data(18)


def test_stationary(vals1):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.aground_check(vals1, 3, 1, 2)
    for i in range(len(vals1)):
        assert vals1.drf_agr == expected_flags[i]


@pytest.fixture
def reps1():
    # stationary drifter
    vals1 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()

    for v in vals1:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary(reps1):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.aground_check(reps1.reps, 3, 1, 2)
    for i in range(0, len(reps1)):
        assert reps1.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps2():
    # stationary drifter (artificial 'jitter' spikes)
    vals2 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 1.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": 1.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]
    reps = ex.Voyage()
    for v in vals2:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary_jitter_spikes(reps2):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.aground_check(reps2.reps, 3, 1, 2)
    for i in range(0, len(reps2)):
        assert reps2.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps3():
    # stationary drifter (artificial 'jitter' which won't be fully smoothed and outside tolerance)
    vals3 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 1.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 1.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]
    reps = ex.Voyage()

    for v in vals3:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary_big_remaining_jitter(reps3):
    expected_flags = [0, 0, 0, 0, 1, 1, 1]
    otqc.aground_check(reps3.reps, 3, 1, 2)
    for i in range(0, len(reps3)):
        assert reps3.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps4():
    # stationary drifter (artificial 'jitter' which won't be fully smoothed and within tolerance)
    vals4 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.01,
            "LON": 0.01,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.01,
            "LON": 0.01,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]
    reps = ex.Voyage()
    for v in vals4:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary_small_remaining_jitter(reps4):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.aground_check(reps4.reps, 3, 1, 2)
    for i in range(0, len(reps4)):
        assert reps4.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps5():
    # moving drifter (going west)
    vals5 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.02,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.04,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.06,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.08,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.10,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.12,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()
    for v in vals5:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_moving_west(reps5):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.aground_check(reps5.reps, 3, 1, 2)
    for i in range(0, len(reps5)):
        assert reps5.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps6():
    # moving drifter (going north)
    vals6 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.02,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.04,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.06,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.08,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.10,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.12,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()
    for v in vals6:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_moving_north(reps6):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.aground_check(reps6.reps, 3, 1, 2)
    for i in range(0, len(reps6)):
        assert reps6.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps7():
    # runs aground (drifter going north then stops)
    vals7 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.02,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.04,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.06,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.08,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.08,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.08,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]
    reps = ex.Voyage()
    for v in vals7:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)
    return reps


def test_moving_north_then_stop(reps7):
    expected_flags = [0, 0, 0, 0, 1, 1, 1]
    otqc.aground_check(reps7.reps, 3, 1, 2)
    for i in range(0, len(reps7)):
        assert reps7.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps8():
    # stationary drifter (high frequency sampling prevents detection)
    vals8 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 1,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 2,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 3,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 4,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 5,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 6,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 7,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()
    for v in vals8:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary_high_freq_sampling(reps8):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.aground_check(reps8.reps, 3, 1, 2)
    for i in range(0, len(reps8)):
        assert reps8.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps9():
    # stationary drifter (low frequency sampling prevents detection)
    vals9 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 10,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 13,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 16,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 19,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]
    reps = ex.Voyage()
    for v in vals9:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary_low_freq_sampling(reps9):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.aground_check(reps9.reps, 3, 1, 2)
    for i in range(0, len(reps9)):
        assert reps9.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps10():
    # stationary drifter (mid frequency sampling enables detection)
    vals10 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 0,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 0,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 9,
            "HR": 0,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 10,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()

    for v in vals10:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary_mid_freq_sampling(reps10):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.aground_check(reps10.reps, 3, 1, 2)
    for i in range(0, len(reps10)):
        assert reps10.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps11():
    # stationary drifter (changed sampling prevents early detection)
    vals11 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 8,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 9,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 10,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 11,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()

    for v in vals11:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stationary_low_to_mid_freq_sampling(reps11):
    expected_flags = [0, 0, 1, 1, 1, 1, 1]
    otqc.aground_check(reps11.reps, 3, 1, 2)
    for i in range(0, len(reps11)):
        assert reps11.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps12():
    # moving drifter (going northwest at equator but going slowly and within tolerance)
    vals12 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.005,
            "LON": -0.005,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.01,
            "LON": -0.01,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.015,
            "LON": -0.015,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.02,
            "LON": -0.02,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.025,
            "LON": -0.025,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.03,
            "LON": -0.03,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()  #

    for v in vals12:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)
    return reps


def test_moving_slowly_northwest(reps12):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.aground_check(reps12.reps, 3, 1, 2)
    for i in range(0, len(reps12)):
        assert reps12.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps13():
    # moving drifter (going west in high Arctic but going slower than tolerance set at equator)
    vals13 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 85.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 85.0,
            "LON": -0.02,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 85.0,
            "LON": -0.04,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 85.0,
            "LON": -0.06,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 85.0,
            "LON": -0.08,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 85.0,
            "LON": -0.10,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 85.0,
            "LON": -0.12,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()
    for v in vals13:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_moving_slowly_west_in_arctic(reps13):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.aground_check(reps13.reps, 3, 1, 2)
    for i in range(0, len(reps13)):
        assert reps13.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps14():
    # stationary then moves
    vals14 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.02,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.04,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.06,
            "LON": 0.0,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()

    for v in vals14:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_stop_then_moving_north(reps14):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.aground_check(reps14.reps, 3, 1, 2)
    for i in range(0, len(reps14)):
        assert reps14.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps15():
    # too short for QC
    vals15 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.02,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()

    for v in vals15:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


import os
import sys


def test_too_short_for_qc(reps15):
    expected_flags = [0, 0]
    old_stdout = sys.stdout
    f = open(os.devnull, "w")
    sys.stdout = f
    otqc.aground_check(reps15.reps, 3, 1, 2)
    sys.stdout = old_stdout
    for i in range(0, len(reps15)):
        assert reps15.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps16():
    # assertion error - bad input parameter
    vals16 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.02,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.04,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.06,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.08,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.10,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.12,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()
    for v in vals16:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_error_bad_input_parameter(reps16):
    expected_flags = [9, 9, 9, 9, 9, 9, 9]
    try:
        otqc.aground_check(reps16.reps, 0, 1, 2)
    except AssertionError as error:
        error_return_text = "invalid input parameter: smooth_win must be >= 1"
        assert str(error)[0 : len(error_return_text)] == error_return_text
    for i in range(0, len(reps16)):
        assert reps16.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps17():
    # assertion error - missing observation
    vals17 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.02,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.04,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 4,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.06,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.08,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.10,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.12,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()
    for v in vals17:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)
    reps.setvar(1, "LON", None)

    return reps


def test_error_missing_observation(reps17):
    expected_flags = [9, 9, 9, 9, 9, 9, 9]
    try:
        otqc.aground_check(reps17.reps, 3, 1, 2)
    except AssertionError as error:
        error_return_text = "problem with report values: Nan(s) found in longitude"
        assert str(error)[0 : len(error_return_text)] == error_return_text
    for i in range(0, len(reps17)):
        assert reps17.get_qc(i, "POS", "drf_agr") == expected_flags[i]


@pytest.fixture
def reps18():
    # assertion error - times not sorted
    vals18 = [
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 1,
            "HR": 12,
            "LAT": 0.0,
            "LON": 0.0,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.02,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 3,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.04,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 2,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.06,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 5,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.08,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 6,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.10,
            "SST": 5.0,
        },
        {
            "ID": "AAAAAAAAA",
            "YR": 2003,
            "MO": 12,
            "DY": 7,
            "HR": 12,
            "LAT": 0.0,
            "LON": -0.12,
            "SST": 5.0,
        },
    ]

    reps = ex.Voyage()

    for v in vals18:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReportQC(rec)
        reps.add_report(rep)

    return reps


def test_error_not_time_sorted(reps18):
    expected_flags = [9, 9, 9, 9, 9, 9, 9]
    try:
        otqc.aground_check(reps18.reps, 3, 1, 2)
    except AssertionError as error:
        error_return_text = "problem with report values: times are not sorted"
        assert str(error)[0 : len(error_return_text)] == error_return_text
    for i in range(0, len(reps18)):
        assert reps18.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary(reps1):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.new_aground_check(reps1.reps, 3, 1)
    for i in range(0, len(reps1)):
        assert reps1.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary_jitter_spikes(reps2):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.new_aground_check(reps2.reps, 3, 1)
    for i in range(0, len(reps2)):
        assert reps2.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary_big_remaining_jitter(reps3):
    expected_flags = [0, 0, 0, 0, 1, 1, 1]
    otqc.new_aground_check(reps3.reps, 3, 1)
    for i in range(0, len(reps3)):
        assert reps3.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary_small_remaining_jitter(reps4):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.new_aground_check(reps4.reps, 3, 1)
    for i in range(0, len(reps4)):
        assert reps4.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_moving_west(reps5):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.new_aground_check(reps5.reps, 3, 1)
    for i in range(0, len(reps5)):
        assert reps5.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_moving_north(reps6):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.new_aground_check(reps6.reps, 3, 1)
    for i in range(0, len(reps6)):
        assert reps6.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_moving_north_then_stop(reps7):
    expected_flags = [0, 0, 0, 0, 1, 1, 1]
    otqc.new_aground_check(reps7.reps, 3, 1)
    for i in range(0, len(reps7)):
        assert reps7.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary_high_freq_sampling(reps8):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.new_aground_check(reps8.reps, 3, 1)
    for i in range(0, len(reps8)):
        assert reps8.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary_low_freq_sampling(reps9):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.new_aground_check(reps9.reps, 3, 1)
    for i in range(0, len(reps9)):
        assert reps9.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary_mid_freq_sampling(reps10):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.new_aground_check(reps10.reps, 3, 1)
    for i in range(0, len(reps10)):
        assert reps10.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stationary_low_to_mid_freq_sampling(reps11):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.new_aground_check(reps11.reps, 3, 1)
    for i in range(0, len(reps11)):
        assert reps11.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_moving_slowly_northwest(reps12):
    expected_flags = [0, 0, 0, 1, 1, 1, 1]
    otqc.new_aground_check(reps12.reps, 3, 1)
    for i in range(0, len(reps12)):
        assert reps12.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_moving_slowly_west_in_arctic(reps13):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    otqc.new_aground_check(reps13.reps, 3, 1)
    for i in range(0, len(reps13)):
        assert reps13.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_stop_then_moving_north(reps14):
    expected_flags = [0, 0, 0, 0, 0, 0, 0]
    otqc.new_aground_check(reps14.reps, 3, 1)
    for i in range(0, len(reps14)):
        assert reps14.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_too_short_for_qc(reps15):
    expected_flags = [0, 0]
    old_stdout = sys.stdout
    f = open(os.devnull, "w")
    sys.stdout = f
    otqc.new_aground_check(reps15.reps, 3, 1)
    sys.stdout = old_stdout
    for i in range(0, len(reps15)):
        assert reps15.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_error_bad_input_parameter(reps16):
    expected_flags = [9, 9, 9, 9, 9, 9, 9]
    try:
        otqc.new_aground_check(reps16.reps, 2, 1)
    except AssertionError as error:
        error_return_text = "invalid input parameter: smooth_win must be an odd number"
        assert str(error)[0 : len(error_return_text)] == error_return_text
    for i in range(0, len(reps16)):
        assert reps16.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_error_missing_observation(reps17):
    expected_flags = [9, 9, 9, 9, 9, 9, 9]
    try:
        otqc.new_aground_check(reps17.reps, 3, 1)
    except AssertionError as error:
        error_return_text = "problem with report values: Nan(s) found in longitude"
        assert str(error)[0 : len(error_return_text)] == error_return_text
    for i in range(0, len(reps17)):
        assert reps17.get_qc(i, "POS", "drf_agr") == expected_flags[i]


def test_new_error_not_time_sorted(reps18):
    expected_flags = [9, 9, 9, 9, 9, 9, 9]
    try:
        otqc.new_aground_check(reps18.reps, 3, 1)
    except AssertionError as error:
        error_return_text = "problem with report values: times are not sorted"
        assert str(error)[0 : len(error_return_text)] == error_return_text
    for i in range(0, len(reps18)):
        assert reps18.get_qc(i, "POS", "drf_agr") == expected_flags[i]
