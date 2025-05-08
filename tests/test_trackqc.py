from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import glamod_marine_processing.qc_suite.modules.next_level_trackqc as tqc
import glamod_marine_processing.qc_suite.modules.trackqc as otqc
from glamod_marine_processing.qc_suite.modules.next_level_track_check_qc import (
    calculate_speed_course_distance_time_difference,
)


def test_daytime_exeter():
    daytime = tqc.track_day_test(2019, 6, 21, 12.0, 50.7, -3.5, elevdlim=-2.5)
    assert daytime


def test_nighttime_exeter():
    daytime = tqc.track_day_test(2019, 6, 21, 0.0, 50.7, -3.5, elevdlim=-2.5)
    assert not (daytime)


def test_large_elevdlim_exeter():
    daytime = tqc.track_day_test(2019, 6, 21, 12.0, 50.7, -3.5, elevdlim=89.0)
    assert not (daytime)


def test_error_invalid_parameter():
    with pytest.raises(ValueError):
        daytime = tqc.track_day_test(2019, 13, 21, 0.0, 50.7, -3.5, elevdlim=-2.5)


def test_no_trim():
    arr = np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    trim = tqc.trim_mean(arr, 0)
    assert trim == 4.0
    assert np.all(
        arr == np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    )  # this checks the array is not modifed by the function


def test_with_trim():
    arr = np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    trim = tqc.trim_mean(arr, 5)
    assert trim == 3.0
    assert np.all(
        arr == np.array([10.0, 4.0, 3.0, 2.0, 1.0])
    )  # this checks the array is not modifed by the function


def test_sd_no_trim():
    arr = np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    trim = tqc.trim_std(arr, 0)
    assert trim == 2.0
    assert np.all(
        arr == np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    )  # this checks the array is not modifed by the function


def test_sd_with_trim():
    arr = np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    trim = tqc.trim_std(arr, 5)
    assert trim == 0.0
    assert np.all(
        arr == np.array([6.0, 1.0, 1.0, 1.0, 1.0])
    )  # this checks the array is not modifed by the function


def test_data(selection):
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
    return test_data(1)


@pytest.fixture
def vals2():
    return test_data(2)


@pytest.fixture
def vals3():
    return test_data(3)


@pytest.fixture
def vals4():
    return test_data(4)


@pytest.fixture
def vals5():
    return test_data(5)


@pytest.fixture
def vals6():
    return test_data(6)


@pytest.fixture
def vals7():
    return test_data(7)


@pytest.fixture
def vals8():
    return test_data(8)


@pytest.fixture
def vals9():
    return test_data(9)


@pytest.fixture
def vals10():
    return test_data(10)


@pytest.fixture
def vals11():
    return test_data(11)


@pytest.fixture
def vals12():
    return test_data(12)


@pytest.fixture
def vals13():
    return test_data(13)


@pytest.fixture
def vals14():
    return test_data(14)


@pytest.fixture
def vals15():
    return test_data(15)


@pytest.fixture
def vals16():
    return test_data(16)


@pytest.fixture
def vals17():
    return test_data(17)


@pytest.fixture
def vals18():
    return test_data(18)


def test_stationary(vals1):
    expected_flags = [1, 1, 1, 1, 1, 1, 1]
    tqc.aground_check(vals1, 3, 1, 2)
    for i in range(len(vals1)):
        assert vals1.drf_agr == expected_flags[i]


import glamod_marine_processing.qc_suite.modules.Extended_IMMA as ex
from glamod_marine_processing.qc_suite.modules.IMMA1 import IMMA


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


# #stationary drifter (artificial 'jitter' spikes)
# vals2 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':1.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.0, 'LON':1.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0}]
#
# #stationary drifter (artificial 'jitter' which won't be fully smoothed and outside tolerance)
# vals3 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':1.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':1.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0}]
#
# #stationary drifter (artificial 'jitter' which won't be fully smoothed and within tolerance)
# vals4 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.01, 'LON':0.01, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.01, 'LON':0.01, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0}]
#
# #moving drifter (going west)
# vals5 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':-0.02, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.0, 'LON':-0.04, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':-0.06, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.0, 'LON':-0.08, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.0, 'LON':-0.10, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':-0.12, 'SST':5.0}]
#
# #moving drifter (going north)
# vals6 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.02, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.04, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.06, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.08, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.10, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.12, 'LON':0.0, 'SST':5.0}]
#
# #runs aground (drifter going north then stops)
# vals7 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.02, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.04, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.06, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.08, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.08, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.08, 'LON':0.0, 'SST':5.0}]
#
# #stationary drifter (high frequency sampling prevents detection)
# vals8 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':1, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':2, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':3, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':4, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':5, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':6, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':7, 'LAT':0.0, 'LON':0.0, 'SST':5.0}]
#
# #stationary drifter (low frequency sampling prevents detection)
# vals9 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':10, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':13, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':16, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':19, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0}]
#
# #stationary drifter (mid frequency sampling enables detection)
# vals10 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':0, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':0, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':9, 'HR':0, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':10, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0}]
#
# #stationary drifter (changed sampling prevents early detection)
# vals11 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':8, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':9, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':10, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':11, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0}]
#
# #moving drifter (going northwest at equator but going slowly and within tolerance)
# vals12 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.005, 'LON':-0.005, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.01, 'LON':-0.01, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.015, 'LON':-0.015, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.02, 'LON':-0.02, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.025, 'LON':-0.025, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.03, 'LON':-0.03, 'SST':5.0}]
#
# #moving drifter (going west in high Arctic but going slower than tolerance set at equator)
# vals13 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':85.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':85.0, 'LON':-0.02, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':85.0, 'LON':-0.04, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':85.0, 'LON':-0.06, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':85.0, 'LON':-0.08, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':85.0, 'LON':-0.10, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':85.0, 'LON':-0.12, 'SST':5.0}]
#
# #stationary then moves
# vals14 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.02, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.04, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.06, 'LON':0.0, 'SST':5.0}]
#
# #too short for QC
# vals15 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':-0.02, 'SST':5.0}]
#
# #assertion error - bad input parameter
# vals16 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':-0.02, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.0, 'LON':-0.04, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':-0.06, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.0, 'LON':-0.08, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.0, 'LON':-0.10, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':-0.12, 'SST':5.0}]
#
# #assertion error - missing observation
# vals17 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':-0.02, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.0, 'LON':-0.04, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':4, 'HR':12, 'LAT':0.0, 'LON':-0.06, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.0, 'LON':-0.08, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.0, 'LON':-0.10, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':-0.12, 'SST':5.0}]
#
# #assertion error - times not sorted
# vals18 = [{'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':1, 'HR':12, 'LAT':0.0, 'LON':0.0, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':-0.02, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':3, 'HR':12, 'LAT':0.0, 'LON':-0.04, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':2, 'HR':12, 'LAT':0.0, 'LON':-0.06, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':5, 'HR':12, 'LAT':0.0, 'LON':-0.08, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':6, 'HR':12, 'LAT':0.0, 'LON':-0.10, 'SST':5.0},
#          {'ID':'AAAAAAAAA', 'YR':2003, 'MO':12, 'DY':7, 'HR':12, 'LAT':0.0, 'LON':-0.12, 'SST':5.0}]
#
# self.reps2 = ex.Voyage()
# self.reps3 = ex.Voyage()
# self.reps4 = ex.Voyage()
# self.reps5 = ex.Voyage()
# self.reps6 = ex.Voyage()
# self.reps7 = ex.Voyage()
# self.reps8 = ex.Voyage()
# self.reps9 = ex.Voyage()
# self.reps10 = ex.Voyage()
# self.reps11 = ex.Voyage()
# self.reps12 = ex.Voyage()
# self.reps13 = ex.Voyage()
# self.reps14 = ex.Voyage()
# self.reps15 = ex.Voyage()
# self.reps16 = ex.Voyage()
# self.reps17 = ex.Voyage()
# self.reps18 = ex.Voyage()
#
#
# for v in vals2:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps2.add_report(rep)
#
# for v in vals3:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps3.add_report(rep)
#
# for v in vals4:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps4.add_report(rep)
#
# for v in vals5:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps5.add_report(rep)
#
# for v in vals6:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps6.add_report(rep)
#
# for v in vals7:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps7.add_report(rep)
#
# for v in vals8:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps8.add_report(rep)
#
# for v in vals9:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps9.add_report(rep)
#
# for v in vals10:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps10.add_report(rep)
#
# for v in vals11:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps11.add_report(rep)
#
# for v in vals12:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps12.add_report(rep)
#
# for v in vals13:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps13.add_report(rep)
#
# for v in vals14:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps14.add_report(rep)
#
# for v in vals15:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps15.add_report(rep)
#
# for v in vals16:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps16.add_report(rep)
#
# for v in vals17:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps17.add_report(rep)
# self.reps17.setvar(1,'LON',None)
#
# for v in vals18:
#     rec = IMMA()
#     for key in v:
#         rec.data[key] = v[key]
#     rep = ex.MarineReportQC(rec)
#     self.reps18.add_report(rep)
