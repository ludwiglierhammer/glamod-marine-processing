from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from glamod_marine_processing.qc_suite.modules.next_level_track_check_qc import (
    calc_alternate_speeds,
    calculate_speed_course_distance_time_difference,
    distr1,
    distr2,
    km_to_nm,
    row_difference,
    spike_check,
    track_check,
)


def generic_frame(in_pt):
    pt = [in_pt for _ in range(30)]
    lat = [-5.0 + i * 0.1 for i in range(30)]
    lon = [0 for _ in range(30)]
    sst = [22 for _ in range(30)]
    sst[15] = 33

    vsi = [11.11951 * km_to_nm for _ in range(30)]
    dsi = [0 for _ in range(30)]
    dck = [193 for _ in range(30)]

    date = pd.date_range(start=f"1850-01-01", freq="1h", periods=len(pt))

    df = pd.DataFrame(
        {
            "sst": sst,
            "date": date,
            "lat": lat,
            "lon": lon,
            "pt": pt,
            "vsi": vsi,
            "dsi": dsi,
            "dck": dck,
        }
    )

    id = ["GOODTHING" for _ in range(30)]

    df["id"] = id

    return df


@pytest.fixture
def ship_frame():
    return generic_frame(1)


@pytest.fixture
def buoy_frame():
    return generic_frame(6)


def test_spike_check(ship_frame, buoy_frame):
    for frame in [ship_frame, buoy_frame]:
        result = spike_check(frame)
        for i in range(30):
            row = result.iloc[i]
            if i == 15:
                assert row.spike == 1
            else:
                assert row.spike == 0


@pytest.mark.parametrize("key", ["sst", "lat", "lon", "pt", "date"])
def test_spike_check_raises(ship_frame, key):
    ship_frame.drop(labels=[key], axis=1, inplace=True)
    with pytest.raises(KeyError):
        spike_check(ship_frame)


def test_row_difference(ship_frame):
    earlier = ship_frame.iloc[0]
    later = ship_frame.iloc[1]

    speed, distance, course, timediff = row_difference(later, earlier)

    assert pytest.approx(speed, 0.00001) == 11.119508064776555
    assert pytest.approx(distance, 0.00001) == 11.119508064776555
    assert course == 0.0
    assert pytest.approx(timediff, 0.0000001) == 1.0


def test_track_check(ship_frame):
    result = track_check(ship_frame)
    for i in range(len(result)):
        assert result.iloc[i].trk == 0

    lon = ship_frame.lon.array
    lon[15] = 30.0
    ship_frame["lon"] = lon
    result = track_check(ship_frame)
    for i in range(len(result)):
        if i == 15:
            assert result.iloc[i].trk == 1
        else:
            assert result.iloc[i].trk == 0


@pytest.mark.parametrize("key", ["lat", "lon", "pt", "date"])
def test_track_check_raises(ship_frame, key):
    ship_frame.drop(labels=[key], axis=1, inplace=True)
    with pytest.raises(KeyError):
        _ = track_check(ship_frame)


def test_calculate_speed_course_distance_time_difference(ship_frame):
    result = calculate_speed_course_distance_time_difference(ship_frame)
    numobs = len(result)
    for i in range(numobs):
        row = result.iloc[i]
        if i > 0:
            assert pytest.approx(row.speed, 0.00001) == 11.119508064776555
            assert pytest.approx(row.distance, 0.00001) == 11.119508064776555
            assert (
                pytest.approx(row.course, 0.00001) == 0
                or pytest.approx(row.course, 0.00001) == 360.0
            )
            assert pytest.approx(row.time_diff, 0.0000001) == 1.0
        else:
            assert np.isnan(row.speed)
