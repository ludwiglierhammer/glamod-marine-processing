from datetime import datetime

import py

import numpy as np
import math

import pytest

import glamod_marine_processing.qc_suite.modules.Climatology as clim
import glamod_marine_processing.qc_suite.modules.Extended_IMMA as ex
from glamod_marine_processing.qc_suite.modules.next_level_deck_qc import (
    Np_Super_Ob,
    get_threshold_multiplier,
    mds_buddy_check,
    bayesian_buddy_check,
)

class IMMA:
    def __init__(self):  # Standard instance object
        self.data = {}  # Dictionary to hold the parameter values


@pytest.fixture
def reps():

    vals = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 2, 'LAT': 0.5, 'LON': 20.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 31, 'HR': 2, 'LAT': 1.5, 'LON': 20.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 30, 'HR': 2, 'LAT': 1.5, 'LON': 21.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 29, 'HR': 2, 'LAT': 1.5, 'LON': 19.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 28, 'HR': 2, 'LAT': 0.5, 'LON': 19.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 6, 'HR': 2, 'LAT': 0.5, 'LON': 21.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 7, 'HR': 2, 'LAT': -0.5, 'LON': 20.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 8, 'HR': 2, 'LAT': -0.5, 'LON': 21.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 9, 'HR': 2, 'LAT': -0.5, 'LON': 19.5, 'SST': 2.0}]

    reps = {}
    for key in vals[0]:
        reps[key] = []
    reps["DATE"] = []
    reps["SST_CLIM"] = []

    for v in vals:
        for key in reps:
            if key != "DATE" and key != "SST_CLIM":
                reps[key].append(v[key])

        hour = int(v["HR"])
        minute = 60 * (v["HR"] - hour)
        date = datetime(v["YR"], v["MO"], v["DY"], hour, minute)
        reps["DATE"].append(date)
        reps["SST_CLIM"].append(0.5)

    for key in reps:
        reps[key] = np.array(reps[key])

    return reps


@pytest.fixture
def reps2():

    vals = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 2, 'LAT': 0.5, 'LON': 20.5, 'SST': 5.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 21, 'HR': 2, 'LAT': 1.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 20, 'HR': 2, 'LAT': 1.5, 'LON': 21.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 19, 'HR': 2, 'LAT': 1.5, 'LON': 19.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 18, 'HR': 2, 'LAT': 0.5, 'LON': 19.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 16, 'HR': 2, 'LAT': 0.5, 'LON': 21.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 17, 'HR': 2, 'LAT': -0.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 18, 'HR': 2, 'LAT': -0.5, 'LON': 21.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 19, 'HR': 2, 'LAT': -0.5, 'LON': 19.5, 'SST': 2.0}]

    reps = {}
    for key in vals[0]:
        reps[key] = []
    reps["DATE"] = []
    reps["SST_CLIM"] = []

    for v in vals:
        for key in reps:
            if key != "DATE" and key != "SST_CLIM":
                reps[key].append(v[key])

        hour = int(v["HR"])
        minute = 60 * (v["HR"] - hour)
        date = datetime(v["YR"], v["MO"], v["DY"], hour, minute)
        reps["DATE"].append(date)
        reps["SST_CLIM"].append(0.5)

    for key in reps:
        reps[key] = np.array(reps[key])

    return reps

@pytest.fixture
def reps3():

    vals = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 2, 'LAT': 0.5, 'LON': 20.5, 'SST': 5.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 21, 'HR': 2, 'LAT': 2.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 20, 'HR': 2, 'LAT': 2.5, 'LON': 22.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 19, 'HR': 2, 'LAT': 2.5, 'LON': 18.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 18, 'HR': 2, 'LAT': 0.5, 'LON': 18.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 16, 'HR': 2, 'LAT': 0.5, 'LON': 22.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 17, 'HR': 2, 'LAT': -1.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 18, 'HR': 2, 'LAT': -1.5, 'LON': 22.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 19, 'HR': 2, 'LAT': -1.5, 'LON': 18.5, 'SST': 2.0}]

    reps = {}
    for key in vals[0]:
        reps[key] = []
    reps["DATE"] = []
    reps["SST_CLIM"] = []

    for v in vals:
        for key in reps:
            if key != "DATE" and key != "SST_CLIM":
                reps[key].append(v[key])

        hour = int(v["HR"])
        minute = 60 * (v["HR"] - hour)
        date = datetime(v["YR"], v["MO"], v["DY"], hour, minute)
        reps["DATE"].append(date)
        reps["SST_CLIM"].append(0.5)

    for key in reps:
        reps[key] = np.array(reps[key])

    return reps

@pytest.fixture
def dummy_pentad_stdev():
    return clim.Climatology(np.full([73, 180, 360], 1.5))

@pytest.fixture
def reps4():

    vals = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 2, 'LAT': 0.5, 'LON': 20.5, 'SST': 5.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 21, 'HR': 2, 'LAT': 3.5, 'LON': 20.5, 'SST': 1.9},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 20, 'HR': 2, 'LAT': 3.5, 'LON': 23.5, 'SST': 1.7},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 19, 'HR': 2, 'LAT': 3.5, 'LON': 17.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 18, 'HR': 2, 'LAT': 0.5, 'LON': 17.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 16, 'HR': 2, 'LAT': 0.5, 'LON': 23.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 17, 'HR': 2, 'LAT': -2.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 18, 'HR': 2, 'LAT': -2.5, 'LON': 23.5, 'SST': 2.3},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 19, 'HR': 2, 'LAT': -2.5, 'LON': 17.5, 'SST': 2.1}]

    reps = {}
    for key in vals[0]:
        reps[key] = []
    reps["DATE"] = []
    reps["SST_CLIM"] = []

    for v in vals:
        for key in reps:
            if key != "DATE" and key != "SST_CLIM":
                reps[key].append(v[key])

        hour = int(v["HR"])
        minute = 60 * (v["HR"] - hour)
        date = datetime(v["YR"], v["MO"], v["DY"], hour, minute)
        reps["DATE"].append(date)
        reps["SST_CLIM"].append(0.5)

    for key in reps:
        reps[key] = np.array(reps[key])

    return reps


def test_eight_near_neighbours(dummy_pentad_stdev, reps):

    g = Np_Super_Ob()
    g.add_obs(reps['LAT'], reps['LON'], reps['DATE'], reps['SST']-reps["SST_CLIM"])
    g.get_buddy_limits_with_parameters(
        dummy_pentad_stdev,
        [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
        [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
        [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]]
    )
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)

    assert mn == 1.5
    assert sd == 3.5 * 1.5


def test_eight_distant_near_neighbours(dummy_pentad_stdev, reps2):

    g = Np_Super_Ob()
    g.add_obs(reps2["LAT"], reps2["LON"], reps2["DATE"], reps2["SST"]-reps2["SST_CLIM"])
    g.get_buddy_limits_with_parameters(dummy_pentad_stdev, [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
                                       [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
                                       [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]])
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)

    assert mn == 1.5
    assert sd == 3.5 * 1.5


def test_eight_even_more_distant_near_neighbours(dummy_pentad_stdev, reps3):

    g = Np_Super_Ob()
    g.add_obs(reps3["LAT"], reps3["LON"], reps3["DATE"], reps3["SST"]-reps3["SST_CLIM"])
    g.get_buddy_limits_with_parameters(dummy_pentad_stdev, [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
                                       [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
                                       [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]])
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)
    assert mn == 1.5
    assert sd == 4.0 * 1.5


def test_eight_too_distant_neighbours(dummy_pentad_stdev, reps4):

    g = Np_Super_Ob()
    g.add_obs(reps4["LAT"], reps4["LON"], reps4["DATE"], reps4["SST"] - reps4["SST_CLIM"])
    g.get_buddy_limits_with_parameters(dummy_pentad_stdev,
                                       [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
                                       [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
                                       [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]])
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)
    assert mn == 0.0
    assert sd == 500.0



def test_nobs_limits_not_ascending():
    with pytest.raises(AssertionError):
        multiplier = get_threshold_multiplier(0, [10, 5, 0], [4, 3, 2])


def test_lowest_nobs_limit_not_zero():
    with pytest.raises(AssertionError):
        multiplier = get_threshold_multiplier(1, [1, 5, 10], [4, 3, 2])


def test_simple():
    for n in range(1, 20):
        multiplier = get_threshold_multiplier(n, [0, 5, 10], [4, 3, 2])
        if 1 <= n <= 5:
            assert multiplier == 4.0
        elif 5 < n <= 10:
            assert multiplier == 3.0
        else:
            assert multiplier == 2.0


def test_that_basic_initialisation_works():
    c = ex.ClimVariable(0.0)

    assert c.getclim() == 0.0
    assert c.getclim('clim') == 0.0
    assert c.getclim('stdev') == None

def test_that_initialisation_with_clim_and_stdev_works():
    c = ex.ClimVariable(0.023, 1.1110)
    assert c.getclim() == 0.023
    assert c.getclim('clim') == 0.023
    assert c.getclim('stdev') == 1.1110

def test_setting_variables():
    c = ex.ClimVariable(3.2)
    assert c.getclim('clim') == 3.2
    assert c.getclim('stdev') is None
    c.setclim(5.9, 'clim')
    assert c.getclim('stdev') is None
    assert c.getclim() == 5.9
    c.setclim(12.33, 'stdev')
    assert c.getclim('stdev') == 12.33
    assert c.getclim() == 5.9


@pytest.fixture
def reps_():

    vals = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 12, 'DY': 1, 'HR': 0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 12, 'DY': 1, 'HR': 0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 12, 'DY': 1, 'HR': 10.0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 12, 'DY': 1, 'HR': 10.0, 'LAT': 1.5, 'LON': 0.5, 'SST': 5.0}]

    reps = {}
    for key in vals[0]:
        reps[key] = []
    reps["DATE"] = []
    reps["SST_CLIM"] = []

    for v in vals:
        for key in reps:
            if key != "DATE" and key != "SST_CLIM":
                reps[key].append(v[key])

        hour = int(v["HR"])
        minute = int(60 * (v["HR"] - hour))
        date = datetime(v["YR"], v["MO"], v["DY"], hour, minute)
        reps["DATE"].append(date)
        reps["SST_CLIM"].append(0.5)

    for key in reps:
        reps[key] = np.array(reps[key])

    return reps


@pytest.fixture
def reps2_():
    vals = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 10.0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 31, 'HR': 10.0, 'LAT': 0.5, 'LON': 0.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 10.0, 'LAT': 1.5, 'LON': 0.5, 'SST': 5.0}]

    reps = {}
    for key in vals[0]:
        reps[key] = []
    reps["DATE"] = []
    reps["SST_CLIM"] = []

    for v in vals:
        for key in reps:
            if key != "DATE" and key != "SST_CLIM":
                reps[key].append(v[key])

        hour = int(v["HR"])
        minute = int(60 * (v["HR"] - hour))
        date = datetime(v["YR"], v["MO"], v["DY"], hour, minute)
        reps["DATE"].append(date)
        reps["SST_CLIM"].append(0.5)

    for key in reps:
        reps[key] = np.array(reps[key])

    return reps


@pytest.fixture
def dummy_pentad_stdev_():
    return clim.Climatology(np.full([73, 180, 360], 1.0))

def test_neighbours(reps2_):
    g = Np_Super_Ob()
    g.add_obs(reps2_["LAT"], reps2_["LON"], reps2_["DATE"], reps2_["SST"] - reps2_["SST_CLIM"])
    temp_anom, temp_nobs = g.get_neighbour_anomalies([2, 2, 2], 180, 89, 0)

    assert len(temp_anom) == 2
    assert len(temp_nobs) == 2

    assert 4.5 in temp_anom
    assert 1.5 in temp_anom

    assert temp_nobs[0] == 1
    assert temp_nobs[1] == 1

def test_add_one_maxes_limits(reps_, dummy_pentad_stdev_):

    g = Np_Super_Ob()
    g.add_rep(reps_['LAT'][0], reps_['LON'][0], reps_['DATE'][0].month, reps_['DATE'][0].day,
              reps_['SST'][0] - reps_['SST_CLIM'][0])
    g.take_average()
    g.get_new_buddy_limits(dummy_pentad_stdev_, dummy_pentad_stdev_, dummy_pentad_stdev_)

    mn = g.get_buddy_mean(
        reps_['LAT'][0],
        reps_['LON'][0],
        reps_['DATE'][0].month,
        reps_['DATE'][0].day
    )
    sd = g.get_buddy_stdev(
        reps_['LAT'][0],
        reps_['LON'][0],
        reps_['DATE'][0].month,
        reps_['DATE'][0].day
    )

    assert pytest.approx(sd, 0.0001) == 500
    assert mn == 0.0

def test_add_multiple(reps_, dummy_pentad_stdev_):
    g = Np_Super_Ob()
    g.add_obs(reps_["LAT"], reps_["LON"], reps_["DATE"], reps_["SST"] - reps_["SST_CLIM"])
    g.get_new_buddy_limits(dummy_pentad_stdev_, dummy_pentad_stdev_, dummy_pentad_stdev_)

    mn = g.get_buddy_mean(
        reps_['LAT'][0],
        reps_['LON'][0],
        reps_['DATE'][0].month,
        reps_['DATE'][0].day
    )
    sd = g.get_buddy_stdev(
        reps_['LAT'][0],
        reps_['LON'][0],
        reps_['DATE'][0].month,
        reps_['DATE'][0].day
    )

    assert pytest.approx(sd, 0.0001) == math.sqrt(10.)
    assert mn == 4.5

def test_creation():
    grid = Np_Super_Ob()
    assert isinstance(grid, Np_Super_Ob)

def test_buddy_check(reps_, dummy_pentad_stdev_):

    parameters = {
        "limits": [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
        "number_of_obs_thresholds": [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
        "multipliers": [[4.0, 3.5, 3.0, 2.5],[4.0], [4.0, 3.5, 3.0, 2.5], [4.0]]
    }

    result = mds_buddy_check(
        reps_["LAT"],
        reps_["LON"],
        reps_["DATE"],
        reps_["SST"] - reps_["SST_CLIM"],
        dummy_pentad_stdev_,
        parameters
    )
    print(result)

def test_bayesian_buddy_check(reps_, dummy_pentad_stdev_):

    result = bayesian_buddy_check(
        reps_["LAT"],
        reps_["LON"],
        reps_["DATE"],
        reps_["SST"] - reps_["SST_CLIM"],
        dummy_pentad_stdev_,
        dummy_pentad_stdev_,
        dummy_pentad_stdev_,
    )

    print(result)