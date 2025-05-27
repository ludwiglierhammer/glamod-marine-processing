import py

import numpy as np
import math

import pytest

import glamod_marine_processing.qc_suite.modules.Climatology as clim
import glamod_marine_processing.qc_suite.modules.Extended_IMMA as ex


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

    outreps = []

    for v in vals:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReport(rec)
        rep.add_climate_variable('SST', 0.5)
        outreps.append(rep)

    return outreps

@pytest.fixture
def reps2():

    vals2 = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 2, 'LAT': 0.5, 'LON': 20.5, 'SST': 5.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 21, 'HR': 2, 'LAT': 1.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 20, 'HR': 2, 'LAT': 1.5, 'LON': 21.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 19, 'HR': 2, 'LAT': 1.5, 'LON': 19.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 18, 'HR': 2, 'LAT': 0.5, 'LON': 19.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 16, 'HR': 2, 'LAT': 0.5, 'LON': 21.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 17, 'HR': 2, 'LAT': -0.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 18, 'HR': 2, 'LAT': -0.5, 'LON': 21.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 19, 'HR': 2, 'LAT': -0.5, 'LON': 19.5, 'SST': 2.0}]

    outreps2 = []

    for v in vals2:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReport(rec)
        rep.add_climate_variable('SST', 0.5)
        outreps2.append(rep)

    return outreps2

@pytest.fixture
def reps3():

    vals3 = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 2, 'LAT': 0.5, 'LON': 20.5, 'SST': 5.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 21, 'HR': 2, 'LAT': 2.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 20, 'HR': 2, 'LAT': 2.5, 'LON': 22.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 19, 'HR': 2, 'LAT': 2.5, 'LON': 18.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 18, 'HR': 2, 'LAT': 0.5, 'LON': 18.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 16, 'HR': 2, 'LAT': 0.5, 'LON': 22.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 17, 'HR': 2, 'LAT': -1.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 18, 'HR': 2, 'LAT': -1.5, 'LON': 22.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 19, 'HR': 2, 'LAT': -1.5, 'LON': 18.5, 'SST': 2.0}]

    outreps3 = []

    for v in vals3:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReport(rec)
        rep.add_climate_variable('SST', 0.5)
        outreps3.append(rep)

    return outreps3

@pytest.fixture
def dummy_pentad_stdev():
    return clim.Climatology(np.full([73, 180, 360], 1.5))

@pytest.fixture
def reps4():
    vals4 = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 2, 'LAT': 0.5, 'LON': 20.5, 'SST': 5.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 21, 'HR': 2, 'LAT': 3.5, 'LON': 20.5, 'SST': 1.9},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 20, 'HR': 2, 'LAT': 3.5, 'LON': 23.5, 'SST': 1.7},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 19, 'HR': 2, 'LAT': 3.5, 'LON': 17.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 18, 'HR': 2, 'LAT': 0.5, 'LON': 17.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 16, 'HR': 2, 'LAT': 0.5, 'LON': 23.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 17, 'HR': 2, 'LAT': -2.5, 'LON': 20.5, 'SST': 2.0},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 18, 'HR': 2, 'LAT': -2.5, 'LON': 23.5, 'SST': 2.3},
             {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 19, 'HR': 2, 'LAT': -2.5, 'LON': 17.5, 'SST': 2.1}]

    outreps4 = []

    for v in vals4:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReport(rec)
        rep.add_climate_variable('SST', 0.5)
        outreps4.append(rep)

    return outreps4


def test_eight_near_neighbours(dummy_pentad_stdev, reps):

    g = ex.Np_Super_Ob()
    for rep in reps:
        g.add_rep(rep.lat(),
                  rep.lon(),
                  rep.getvar('YR'),
                  rep.getvar('MO'),
                  rep.getvar('DY'),
                  rep.getanom('SST'))
    g.take_average()
    g.get_buddy_limits_with_parameters(dummy_pentad_stdev, [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
                                       [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
                                       [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]])
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)

    assert mn == 1.5
    assert sd == 3.5 * 1.5


def test_eight_distant_near_neighbours(dummy_pentad_stdev, reps2):

    g = ex.Np_Super_Ob()
    for rep in reps2:
        g.add_rep(rep.lat(),
                  rep.lon(),
                  rep.getvar('YR'),
                  rep.getvar('MO'),
                  rep.getvar('DY'),
                  rep.getanom('SST'))
    g.take_average()
    g.get_buddy_limits_with_parameters(dummy_pentad_stdev, [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
                                       [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
                                       [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]])
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)

    assert mn == 1.5
    assert sd == 3.5 * 1.5

def test_eight_even_more_distant_near_neighbours(dummy_pentad_stdev, reps3):

    g = ex.Np_Super_Ob()
    for rep in reps3:
        g.add_rep(rep.lat(),
                  rep.lon(),
                  rep.getvar('YR'),
                  rep.getvar('MO'),
                  rep.getvar('DY'),
                  rep.getanom('SST'))
    g.take_average()
    g.get_buddy_limits_with_parameters(dummy_pentad_stdev, [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
                                       [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
                                       [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]])
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)
    assert mn == 1.5
    assert sd == 4.0 * 1.5

def test_eight_too_distant_neighbours(dummy_pentad_stdev, reps4):

    g = ex.Np_Super_Ob()
    for rep in reps4:
        g.add_rep(rep.lat(),
                  rep.lon(),
                  rep.getvar('YR'),
                  rep.getvar('MO'),
                  rep.getvar('DY'),
                  rep.getanom('SST'))
    g.take_average()
    g.get_buddy_limits_with_parameters(dummy_pentad_stdev,
                                       [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]],
                                       [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]],
                                       [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]])
    mn = g.get_buddy_mean(0.5, 20.5, 1, 1)
    sd = g.get_buddy_stdev(0.5, 20.5, 1, 1)
    assert mn == 0.0
    assert sd == 500.0


    # multiplier = get_threshold_multiplier(total_nobs,nob_limits,multiplier_values)
def test_nobs_limits_not_ascending():
    with pytest.raises(AssertionError):
        multiplier = ex.get_threshold_multiplier(0, [10, 5, 0], [4, 3, 2])

def test_lowest_nobs_limit_not_zero():
    with pytest.raises(AssertionError):
        multiplier = ex.get_threshold_multiplier(1, [1, 5, 10], [4, 3, 2])

def test_simple():
    for n in range(1, 20):
        multiplier = ex.get_threshold_multiplier(n, [0, 5, 10], [4, 3, 2])
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

    outreps = []

    for v in vals:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReport(rec)
        rep.add_climate_variable('SST', 0.5)
        outreps.append(rep)

    return outreps

@pytest.fixture
def reps2_():
    vals = [{'ID': 'AAAAAAAAA', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 10.0, 'LAT': 0.5, 'LON': 0.5, 'SST': 5.0},
            {'ID': 'BBBBBBBBB', 'YR': 2002, 'MO': 12, 'DY': 31, 'HR': 10.0, 'LAT': 0.5, 'LON': 0.5, 'SST': 2.0},
            {'ID': 'BBBBBBBBB', 'YR': 2003, 'MO': 1, 'DY': 1, 'HR': 10.0, 'LAT': 1.5, 'LON': 0.5, 'SST': 5.0}]

    outreps2 = []
    for v in vals:
        rec = IMMA()
        for key in v:
            rec.data[key] = v[key]
        rep = ex.MarineReport(rec)
        rep.add_climate_variable('SST', 0.5)
        outreps2.append(rep)

    return outreps2

@pytest.fixture
def dummy_pentad_stdev_():
    return clim.Climatology(np.full([73, 180, 360], 1.0))

def test_neighbours(reps2_):
    g = ex.Np_Super_Ob()
    for rep in reps2_:
        g.add_rep(rep.lat(),
                  rep.lon(),
                  rep.getvar('YR'),
                  rep.getvar('MO'),
                  rep.getvar('DY'),
                  rep.getanom('SST'))
    g.take_average()
    temp_anom, temp_nobs = g.get_neighbour_anomalies([2, 2, 2], 180, 89, 0)

    assert len(temp_anom) == 2
    assert len(temp_nobs) == 2

    assert 4.5 in temp_anom
    assert 1.5 in temp_anom

    assert temp_nobs[0] == 1
    assert temp_nobs[1] == 1

def test_add_one_maxes_limits(reps_, dummy_pentad_stdev_):

    g = ex.Np_Super_Ob()
    g.add_rep(reps_[0].lat(), reps_[0].lon(), reps_[0].getvar('YR'), reps_[0].getvar('MO'),
              reps_[0].getvar('DY'), reps_[0].getanom('SST'))
    g.take_average()
    g.get_new_buddy_limits(dummy_pentad_stdev_, dummy_pentad_stdev_, dummy_pentad_stdev_)

    mn = g.get_buddy_mean(reps_[0].getvar('LAT'),
                          reps_[0].getvar('LON'),
                          reps_[0].getvar('MO'),
                          reps_[0].getvar('DY'))
    sd = g.get_buddy_stdev(reps_[0].getvar('LAT'),
                           reps_[0].getvar('LON'),
                           reps_[0].getvar('MO'),
                           reps_[0].getvar('DY'))

    assert pytest.approx(sd, 0.0001) == 500
    assert mn == 0.0

def test_add_multiple(reps_, dummy_pentad_stdev_):
    g = ex.Np_Super_Ob()
    for rep in reps_:
        g.add_rep(rep.getvar('LAT'),
                  rep.getvar('LON'),
                  rep.getvar('YR'),
                  rep.getvar('MO'),
                  rep.getvar('DY'),
                  rep.getanom('SST'))
    g.take_average()
    g.get_new_buddy_limits(dummy_pentad_stdev_, dummy_pentad_stdev_, dummy_pentad_stdev_)

    mn = g.get_buddy_mean(reps_[0].getvar('LAT'),
                          reps_[0].getvar('LON'),
                          reps_[0].getvar('MO'),
                          reps_[0].getvar('DY'))
    sd = g.get_buddy_stdev(reps_[0].getvar('LAT'),
                           reps_[0].getvar('LON'),
                           reps_[0].getvar('MO'),
                           reps_[0].getvar('DY'))

    assert pytest.approx(sd, 0.0001) == math.sqrt(10.)
    assert mn == 4.5

def test_creation():
    _ = ex.Np_Super_Ob()

