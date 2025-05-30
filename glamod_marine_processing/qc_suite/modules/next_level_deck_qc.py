"""Module containing QC functions for deck level QC checks which could be applied on a DataBundle."""

from __future__ import annotations

from typing import Sequence

import math
import numpy as np
import pandas as pd
import pytest

from glamod_marine_processing.qc_suite.modules.location_control import (
    mds_lon_to_xindex,
    mds_lat_to_yindex,
)
from glamod_marine_processing.qc_suite.modules.next_level_trackqc import is_monotonic
from glamod_marine_processing.qc_suite.modules.statistics import p_gross
from glamod_marine_processing.qc_suite.modules.time_control import (
    which_pentad,
    pentad_to_month_day,
)

from glamod_marine_processing.qc_suite.modules.qc import failed, passed, untestable, untested

km_to_nm = 0.539957

def get_threshold_multiplier(total_nobs, nob_limits, multiplier_values):
    """
    Find the highest value of i such that total_nobs is greater
    than nob_limits[i] and return multiplier_values[i]

    :param total_nobs: total number of neighbour observations
    :param nob_limits: list containing the limiting numbers of observations in
                       ascending order first element must be zero
    :param multiplier_values: list containing the multiplier values associated.
    :type total_nobs: integer
    :type nob_limits: List[integer]
    :type multiplier_values: List[float]
    :return: the multiplier value
    :rtype: float

    This routine is used by the buddy check. It's a bit niche.
    """
    assert len(nob_limits) == len(multiplier_values), "length of input lists are different"
    assert min(multiplier_values) > 0, "multiplier value less than zero"
    assert min(nob_limits) == 0, "nob_limit of less than zero given"
    assert nob_limits[0] == 0, "lowest nob_limit not equal to zero"
    assert is_monotonic(nob_limits), "nob_limits not in ascending order"

    multiplier = -1
    if total_nobs == 0:
        multiplier = 4.0

    for i in range(0, len(nob_limits)):
        if total_nobs > nob_limits[i]:
            multiplier = multiplier_values[i]

    assert multiplier > 0, "output multiplier less than or equal to zero "

    return multiplier


class Np_Super_Ob:
    """Class for gridding data in buddy check, based on numpy arrays."""

    def __init__(self):
        self.grid = np.zeros((360, 180, 73))
        self.buddy_mean = np.zeros((360, 180, 73))
        self.buddy_stdev = np.zeros((360, 180, 73))
        self.nobs = np.zeros((360, 180, 73))

    def add_obs(self, lats, lons, dates, anoms):
        n_obs = len(lats)
        for i in range(n_obs):
            self.add_rep(lats[i],lons[i], dates[i].year, dates[i].month, dates[i].day, anoms[i])
        self.take_average()

    def add_rep(self, lat, lon, year, month, day, anom):
        """Add an anomaly to the grid from specified lat lon and date."""
        xindex = mds_lon_to_xindex(lon)
        yindex = mds_lat_to_yindex(lat)
        pindex = which_pentad(month, day) - 1

        assert 0 <= xindex < 360, "bad lon" + str(lon)
        assert 0 <= yindex < 180, "bad lat" + str(lat)
        assert 0 <= pindex < 73, "bad pentad" + str(month) + str(day)

        if anom is not None:
            self.grid[xindex][yindex][pindex] += anom
            self.nobs[xindex][yindex][pindex] += 1

    def take_average(self):
        """Take the average of a grid."""
        nonmiss = np.nonzero(self.nobs)
        self.grid[nonmiss] = self.grid[nonmiss] / self.nobs[nonmiss]

    def get_neighbour_anomalies(self, search_radius, xindex, yindex, pindex):
        """
        Search within a specified search radius of the given point and extract
        the neighbours for buddy check

        :param search_radius: three element array search radius in which to look lon, lat, time
        :param xindex: the xindex of the gridcell to start from
        :param yindex: the yindex of the gridcell to start from
        :param pindex: the pindex of the gridcell to start from
        :return: anomalies and numbers of observations in two lists
        :rtype: list of floats
        """
        assert len(search_radius) == 3, str(len(search_radius))

        radcon = 3.1415928 / 180.0

        latitude_approx = 89.5 - yindex

        xspan = search_radius[0]
        full_xspan = int(xspan / math.cos(latitude_approx * radcon))
        yspan = search_radius[1]
        pspan = search_radius[2]

        temp_anom = []
        temp_nobs = []

        for xpt in range(-1 * full_xspan, full_xspan + 1):
            for ypt in range(-1 * yspan, yspan + 1):
                for ppt in range(-1 * pspan, pspan + 1):
                    if xpt == 0 and ypt == 0 and ppt == 0:
                        continue

                    thisxx = (xindex + xpt) % 360
                    thisyy = (yindex + ypt) % 180
                    thispp = (pindex + ppt) % 73

                    if self.nobs[thisxx][thisyy][thispp] != 0:
                        temp_anom.append(self.grid[thisxx][thisyy][thispp])
                        temp_nobs.append(self.nobs[thisxx][thisyy][thispp])

        return temp_anom, temp_nobs

    def get_buddy_limits_with_parameters(
        self, pentad_stdev, limits, number_of_obs_thresholds, multipliers
    ):
        """Get buddy limits with parameters."""
        nonmiss = np.nonzero(self.nobs)
        for i in range(len(nonmiss[0])):
            xindex = nonmiss[0][i]
            yindex = nonmiss[1][i]
            pindex = nonmiss[2][i]
            m, d = pentad_to_month_day(pindex + 1)

            stdev = pentad_stdev.get_value_mds_style(
                89.5 - yindex, -179.5 + xindex, m, d
            )

            if stdev is None or stdev < 0.0:
                stdev = 1.0

            match_not_found = True

            for j, limit in enumerate(limits):
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    limits[j], xindex, yindex, pindex
                )

                if len(temp_anom) > 0 and match_not_found:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(
                            total_nobs, number_of_obs_thresholds[j], multipliers[j]
                        )
                        * stdev
                    )

                    match_not_found = False

            if match_not_found:
                self.buddy_mean[xindex][yindex][pindex] = 0.0
                self.buddy_stdev[xindex][yindex][pindex] = 500.0

        return

    def get_buddy_limits(self, pentad_stdev):
        """Get buddy limits for old style buddy check."""
        nonmiss = np.nonzero(self.nobs)
        for i in range(len(nonmiss[0])):
            xindex = nonmiss[0][i]
            yindex = nonmiss[1][i]
            pindex = nonmiss[2][i]
            month, day = pentad_to_month_day(pindex + 1)

            # bug noted here single field getsst but multiple fields passed
            stdev = pentad_stdev.get_value_mds_style(
                89.5 - yindex, -179.5 + xindex, month, day
            )

            if stdev is None or stdev < 0.0:
                stdev = 1.0

            match_not_found = True

            # if there is neighbour in that range then calculate a mean
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [1, 1, 2], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(
                            total_nobs, [0, 5, 15, 100], [4.0, 3.5, 3.0, 2.5]
                        )
                        * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # otherwise move out further in space and time to 2 degrees and 2 pentads
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [2, 2, 2], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(total_nobs, [0], [4.0]) * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # otherwise move out further in space and time to 2 degrees and 2 pentads
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [1, 1, 4], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(
                            total_nobs, [0, 5, 15, 100], [4.0, 3.5, 3.0, 2.5]
                        )
                        * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # final step out is to 2 degrees and 4 pentads
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [2, 2, 4], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(total_nobs, [0], [4.0]) * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # if there are no neighbours then any observation will get a pass
            if match_not_found:
                self.buddy_mean[xindex][yindex][pindex] = 0.0
                self.buddy_stdev[xindex][yindex][pindex] = 500.0

        return

    def get_new_buddy_limits(
        self, stdev1, stdev2, stdev3, limits=[2, 2, 4], sigma_m=1.0, noise_scaling=3.0
    ):
        """Get buddy limits for new bayesian buddy check.

        :param stdev1: Field of standard deviations representing standard deviation of difference between target
            gridcell and complete neighbour average (grid area to neighbourhood difference)
        :param stdev2: Field of standard deviations representing standard deviation of difference between a single
            observation and the target gridcell average (point to grid area difference)
        :param stdev3: Field of standard deviations representing standard deviation of difference between random
            neighbour gridcell and full neighbour average (uncertainty in neighbour average)
        :param limits: three membered list of number of degrees in latitude and longitude and number of pentads
        :param sigma_m: Estimated measurement error uncertainty
        :param noise_scaling: scale noise by a factor of noise_scaling used to match observed variability
        :type stdev1: numpy array
        :type stdev2: numpy array
        :type stdev3: numpy array
        :type limits: list of floats
        :type sigma_m: float
        """
        nonmiss = np.nonzero(self.nobs)

        for i in range(len(nonmiss[0])):
            xindex = nonmiss[0][i]
            yindex = nonmiss[1][i]
            pindex = nonmiss[2][i]

            m, d = pentad_to_month_day(pindex + 1)

            stdev1_ex = stdev1.get_value(89.5 - yindex, -179.5 + xindex, m, d)
            stdev2_ex = stdev2.get_value(89.5 - yindex, -179.5 + xindex, m, d)
            stdev3_ex = stdev3.get_value(89.5 - yindex, -179.5 + xindex, m, d)

            if stdev1_ex is None or stdev1_ex < 0.0:
                stdev1_ex = 1.0
            if stdev2_ex is None or stdev2_ex < 0.0:
                stdev2_ex = 1.0
            if stdev3_ex is None or stdev3_ex < 0.0:
                stdev3_ex = 1.0

            # if there is neighbour in that range then calculate a mean
            temp_anom, temp_nobs = self.get_neighbour_anomalies(
                limits, xindex, yindex, pindex
            )

            if len(temp_anom) > 0:
                self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)

                tot = 0.0
                ntot = 0.0
                for n_obs in temp_nobs:
                    # measurement error for each 1x1x5day cell
                    tot += sigma_m**2.0 / n_obs
                    # sampling error for each 1x1x5day cell
                    # multiply by three to match observed stdev
                    tot += noise_scaling * (stdev2_ex**2.0 / n_obs)
                    ntot += 1.0

                sigma_buddy = tot / (ntot**2.0)
                sigma_buddy += stdev3_ex**2.0 / ntot

                self.buddy_stdev[xindex][yindex][pindex] = math.sqrt(
                    sigma_m**2.0
                    + stdev1_ex**2.0
                    + noise_scaling * stdev2_ex**2.0
                    + sigma_buddy
                )

            else:
                self.buddy_mean[xindex][yindex][pindex] = 0.0
                self.buddy_stdev[xindex][yindex][pindex] = 500.0

        return

    def get_buddy_mean(self, lat, lon, month, day):
        """
        Get the buddy mean from the grid for a specified time and place

        :param lat: latitude of the location for which the buddy mean is desired
        :param lon: longitude of the location for which the buddy mean is desired
        :param month: month for which the buddy mean is desired
        :param day: day for which the buddy mean is desired
        :type lat: float
        :type lon: float
        :type month: integer
        :type day: integer
        """
        xindex = mds_lon_to_xindex(lon)
        yindex = mds_lat_to_yindex(lat)
        pindex = which_pentad(month, day) - 1
        return self.buddy_mean[xindex][yindex][pindex]

    def get_buddy_stdev(self, lat, lon, month, day):
        """
        Get the buddy standard deviation from the grid for a specified time and place

        :param lat: latitude of the location for which the buddy standard deviation is desired
        :param lon: longitude of the location for which the buddy standard deviatio is desired
        :param month: month for which the buddy standard deviatio is desired
        :param day: day for which the buddy standard deviatio is desired
        :type lat: float
        :type lon: float
        :type month: integer
        :type day: integer
        """
        xindex = mds_lon_to_xindex(lon)
        yindex = mds_lat_to_yindex(lat)
        pindex = which_pentad(month, day) - 1
        return self.buddy_stdev[xindex][yindex][pindex]


def mds_buddy_check(lats, lons, dates, anoms, pentad_stdev, parameters):
    """
    Do the old style buddy check. Only those observations that pass the QC_filter
    of the class will be buddy checked.

    :param intype: The variable name for the variable that is to be buddy checked.
    :param pentad_stdev: Field of standard deviations of 1x1xpentad standard deviations
    :param parameters: list of parameters for the buddy check
    :type intype: string
    :type pentad_stdev: numpy array
    """
    limits = parameters["limits"]
    number_of_obs_thresholds = parameters["number_of_obs_thresholds"]
    multipliers = parameters["multipliers"]

    # calculate superob averages and numbers of observations
    grid = Np_Super_Ob()
    grid.add_obs(lats, lons, dates, anoms)
    grid.get_buddy_limits_with_parameters(pentad_stdev, limits, number_of_obs_thresholds, multipliers)

    numobs = len(lats)
    qc_outcomes = np.zeros(numobs) + untested

    # finally loop over all reports and update buddy QC
    for i in range(numobs):
        lat = lats[i]
        lon = lons[i]
        mon = dates[i].month
        day = dates[i].day

        # if the SST anomaly differs from the neighbour average by more than the calculated range then reject
        x = anoms[i]
        bm = grid.get_buddy_mean(lat, lon, mon, day)
        bsd = grid.get_buddy_stdev(lat, lon, mon, day)

        qc_outcomes[i] = passed
        if abs(x - bm) >= bsd:
            qc_outcomes[i] = failed

    del grid

    return qc_outcomes

def bayesian_buddy_check(lats, lons, dates, anoms, stdev1, stdev2, stdev3):
    """
    Do the Bayesian buddy check. Only those observations that pass the QC_filter
    of the class will be buddy checked. The bayesian buddy check assigns a
    probability of gross error to each observations, which is rounded down to the
    tenth and then multiplied by 10 to yield a flag between 0 and 9.

    :param intype: The variable name for the variable that is to be buddy checked.
    :param stdev1: Field of standard deviations representing standard deviation of difference between
      target gridcell and complete neighbour average (grid area to neighbourhood difference)
    :param stdev2: Field of standard deviations representing standard deviation of difference between
      a single observation and the target gridcell average (point to grid area difference)
    :param stdev3: Field of standard deviations representing standard deviation of difference between
      random neighbour gridcell and full neighbour average (uncertainty in neighbour average)
    :param parameters: list of parameters
    :type intype: string
    :type stdev1: numpy array
    :type stdev2: numpy array
    :type stdev3: numpy array
    """
    parameters = {
        "bayesian_buddy_check": {
            "prior_probability_of_gross_error": 0.05,
            "quantization_interval": 0.1,
            "limits": [2, 2, 4],
            "noise_scaling": 3.0,
            "measurement_error": 1.0
        },
        "maximum_anomaly": 8.0,
    }

    p0 = parameters["bayesian_buddy_check"]["prior_probability_of_gross_error"]
    q = parameters["bayesian_buddy_check"]["quantization_interval"]
    sigma_m = parameters["bayesian_buddy_check"]["measurement_error"]

    r_hi = parameters["maximum_anomaly"]  # previous upper QC limits set
    r_lo = -1.0 * r_hi  # previous lower QC limit set

    limits = parameters["bayesian_buddy_check"]["limits"]
    noise_scaling = parameters["bayesian_buddy_check"]["noise_scaling"]

    grid = Np_Super_Ob()
    grid.add_obs(lats, lons, dates, anoms)
    grid.get_new_buddy_limits(stdev1, stdev2, stdev3, limits, sigma_m, noise_scaling)

    numobs = len(lats)
    qc_outcomes = np.zeros(numobs) + untested

    for i in range(numobs):
        lat = lats[i]
        lon = lons[i]
        mon = dates[i].month
        day = dates[i].day

        # if the SST anomaly differs from the neighbour average
        # by more than the calculated range then reject

        ppp = p_gross(
            p0,
            q,
            r_hi,
            r_lo,
            anoms[i],
            grid.get_buddy_mean(lat, lon, mon, day),
            grid.get_buddy_stdev(lat, lon, mon, day),
        )

        qc_outcomes[i] = 0
        if ppp > 0:
            flag = int(math.floor(ppp * 10))
            flag = min(flag, 9)
            qc_outcomes[i] = flag

    del grid

    return qc_outcomes