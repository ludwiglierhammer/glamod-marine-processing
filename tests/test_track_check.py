from __future__ import annotations

import pytest
import numpy as np
import math

from glamod_marine_processing.qc_suite.modules.IMMA1 import IMMA

import glamod_marine_processing.qc_suite.modules.Extended_IMMA as ex
import glamod_marine_processing.qc_suite.modules.track_check as tc
import glamod_marine_processing.qc_suite.modules.spherical_geometry as sg

km_to_nm = 0.539957


def test_ship_heading_north_at_60knots_goes1degree_in_1hour():
    """A ship travelling north at 60 knots will go 1 degree in 1 hours"""
    for lat in range(-90, 90):
        alat1 = lat
        alon1 = lat
        avs = 60.0 / km_to_nm
        ads = 0.0
        timdif = 2.0
        alat2, alon2 = tc.increment_position(alat1, alon1, avs, ads, timdif)
        assert pytest.approx(alon2, 0.001) == 0
        assert pytest.approx(alat2, 0.001) == 1


def test_ship_heading_east_at_60knots_goes1degree_in_1hour():
    """A ship at the equator travelling east at 60 knots will go 1 degree in 1 hour"""
    km_to_nm = 0.539957
    alat1 = 0.0
    alat2 = 0.0
    avs = 60.0 / km_to_nm
    ads = 90.0
    timdif = 2.0
    aud1, avd1 = tc.increment_position(alat1, alat2, avs, ads, timdif)
    assert pytest.approx(avd1, 0.001) == 1
    assert pytest.approx(aud1, 0.001) == 0


def test_ship_heading_east_at_60knots_at_latitude60_goes2degrees_in_1hour():
    """A ship travelling east at 60 knots will go 2 degrees in 1 hour at 60N"""
    km_to_nm = 0.539957
    alat = 60.0
    alon = 0.0
    avs = 60.0 / km_to_nm
    ads = 90.0
    timdif = 2.0
    dlat, dlon = tc.increment_position(alat, alon, avs, ads, timdif)
    distance = sg.sphere_distance(alat, alon, alat + dlat, alon + dlon) * km_to_nm
    assert pytest.approx(distance, 0.0001) == 60.0


def test_ship_goes_southwest():
    alat1 = 0.0
    alat2 = 0.0
    avs = 60.0 / km_to_nm
    ads = 225.0
    timdif = 2.0
    aud1, avd1 = tc.increment_position(alat1, alat2, avs, ads, timdif)
    assert pytest.approx(avd1, 0.001) == -1. / np.sqrt(2)
    assert pytest.approx(aud1, 0.001) == -1. / np.sqrt(2)


def test_noinput():
    m = tc.modesp([])
    assert m is None


def test_one_input():
    m = tc.modesp([17.0])
    assert m is None


def test_single_speed_input_over8point5():
    speeds = [20.0 / km_to_nm for i in range(8)]
    m = tc.modesp(speeds)
    assert m == 19.5 / km_to_nm


def test_single_speed_input_under8point5():
    speeds = [2.0 / km_to_nm for i in range(8)]
    m = tc.modesp(speeds)
    assert m == 8.5 / km_to_nm


def test_single_speed_input_overmaximum():
    speeds = [200.0 / km_to_nm for i in range(8)]
    m = tc.modesp(speeds)
    assert m == 34.5 / km_to_nm


def test_one_of_each_speed_input_min_under8point5():
    speeds = [i / km_to_nm for i in range(1, 20)]
    m = tc.modesp(speeds)
    assert m == 8.5 / km_to_nm


# rec = IMMA()
# v = {'ID':'SHIP1   ', 'YR':2001, 'MO':1, 'DY':1, 'HR':hour, 'LAT': hour*speed1/60., 'LON':0.0, 'DS':8, 'VS':4 }
# for key in v: rec.data[key] = v[key]
# .trip1.add_report(ex.MarineReport(rec))
# shipid, lat, lon, sst, mat, year, month, day, hour, icoads_ds, icoads_vs, uid

@pytest.fixture()
def trip1():
    _trip1 = ex.Voyage()
    speed1 = 18. / km_to_nm
    for hour in range(0, 24):
        rec = IMMA()
        v = {
            'ID': 'SHIP1    ',
            'YR': 2001,
            'MO': 1,
            'DY': 1,
            'HR': hour,
            'LAT': hour * speed1 * 360. / (2 * np.pi * 6371.0088),
            'LON': 0.0,
            'DS': 8,
            'VS': 4
        }
        for key in v:
            rec.data[key] = v[key]
        _trip1.add_report(ex.MarineReport(rec))

    return _trip1


@pytest.fixture()
def trip2():
    _trip2 = ex.Voyage()
    speed1 = 18. / km_to_nm
    for hour in range(0, 3):
        rec = IMMA()
        v = {
            'ID': 'SHIP1    ',
            'YR': 2001,
            'MO': 1,
            'DY': 1,
            'HR': hour,
            'LAT': hour * speed1 * 360. / (2 * np.pi * 6371.0088),
            'LON': 0.0,
            'DS': 8,
            'VS': 4
        }
        for key in v:
            rec.data[key] = v[key]
        _trip2.add_report(ex.MarineReport(rec))
    _trip2.reps[1].setvar('LON', 1.0)

    return _trip2


def test_first_entry_missing(trip1):
    difference_from_estimated_location = tc.distr1(trip1)
    assert difference_from_estimated_location[0] == None


def test_ship_is_at_computed_location(trip1):
    difference_from_estimated_location = tc.distr1(trip1)
    for i, diff in enumerate(difference_from_estimated_location):
        if 0 < i < len(difference_from_estimated_location) - 1:
            assert pytest.approx(diff, 1) == 0


def test_misplaced_ob_out_by_1degree_times_coslat(trip2):
    difference_from_estimated_location = tc.distr1(trip2)
    expected = (2 * np.pi * 6371.0088) * np.cos(trip2.reps[1].lat() * np.pi / 180.) / 360
    assert pytest.approx(difference_from_estimated_location[1], 0.00001) == expected


def test_last_entry_missing_1(trip1):
    difference_from_estimated_location = tc.distr2(trip1)
    assert difference_from_estimated_location[-1] is None


def test_ship_is_at_computed_location_1(trip1):
    difference_from_estimated_location = tc.distr2(trip1)
    for i, diff in enumerate(difference_from_estimated_location):
        if 0 < i < len(difference_from_estimated_location) - 1:
            assert pytest.approx(diff, 1) == 0


def test_misplaced_ob_out_by_1degree_times_coslat_1(trip2):
    difference_from_estimated_location = tc.distr2(trip2)
    expected = (2 * np.pi * 6371.0088) * np.cos(trip2.reps[1].lat() * np.pi / 180.) / 360.
    assert pytest.approx(difference_from_estimated_location[1], 0.00001) == expected


def test_first_and_last_are_missing_2(trip1):
    midpoint_discrepancies = tc.midpt(trip1)
    assert midpoint_discrepancies[0] is None
    assert midpoint_discrepancies[-1] is None


def test_midpt_1_deg_error_out_by_60coslat_2(trip2):
    midpoint_discrepancies = tc.midpt(trip2)
    assert pytest.approx(midpoint_discrepancies[1], 0.00001) == (2 * np.pi * 6371.0088) * math.cos(
        trip2.reps[1].lat() * np.pi / 180) / 360.


def test_midpt_at_computed_location_2(trip1):
    midpoint_discrepancies = tc.midpt(trip1)
    for i, pt in enumerate(midpoint_discrepancies):
        if 0 < i < len(midpoint_discrepancies) - 1:
            assert pt is not None
            assert pytest.approx(pt, 1) == 0


def test_just_pass_and_just_fail():
    for angle in [0, 45, 90, 135, 180, 225, 270, 315, 360]:
        assert 10 == tc.direction_continuity(angle, angle, angle + 60.1)
        assert 0 == tc.direction_continuity(angle, angle, angle + 59.9)


def test_1():
    result = tc.speed_continuity(12, 12, 12 / km_to_nm)
    assert result == 0


def test_just_fails():
    result = tc.speed_continuity(12, 12, (12 + 10.01) / km_to_nm)
    assert result == 10


def test_just_passes():
    result = tc.speed_continuity(12, 12, (12 + 9.99) / km_to_nm)
    assert result == 0


def test_input_speed_is_None():
    result = tc.speed_continuity(12, 12, None)
    assert result == 0
