"""Module containing QC functions for deck level QC checks which could be applied on a DataBundle."""

from __future__ import annotations

import itertools
from datetime import datetime
from typing import Sequence

import math
import numpy as np

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
import glamod_marine_processing.qc_suite.modules.Climatology as clim
from glamod_marine_processing.qc_suite.modules.Climatology import Climatology
from glamod_marine_processing.qc_suite.modules.auxiliary import (
    failed,
    passed,
    untested,
    inspect_arrays,
)

km_to_nm = 0.539957


def get_threshold_multiplier(total_nobs: int, nob_limits: list[int], multiplier_values: list[float]) -> float:
    """Find the highest value of i such that total_nobs is greater than nob_limits[i] and return multiplier_values[i]

    This routine is used by the buddy check. It's a bit niche.

    Parameters
    ----------
    total_nobs: int
        total number of neighbour observations
    nob_limits: list[int]
        list containing the limiting numbers of observations in ascending order first element must be zero
    multiplier_values: list[float]
        list containing the multiplier values associated.

    Returns
    -------
    float
        the multiplier value
    """
    assert len(nob_limits) == len(
        multiplier_values
    ), "length of input lists are different"
    assert min(multiplier_values) > 0, "multiplier value less than zero"
    assert min(nob_limits) == 0, "nob_limit of less than zero given"
    assert nob_limits[0] == 0, "lowest nob_limit not equal to zero"
    assert is_monotonic(nob_limits), "nob_limits not in ascending order"

    multiplier = -1
    if total_nobs == 0:
        multiplier = 4.0

    for i, limit in enumerate(nob_limits):
        if total_nobs > limit:
            multiplier = multiplier_values[i]

    assert multiplier > 0, "output multiplier less than or equal to zero "

    return multiplier


class SuperObsGrid:
    """Class for gridding data in buddy check, based on numpy arrays."""

    def __init__(self):
        """Initialise empty grid"""
        self.grid = np.zeros((360, 180, 73))  # type: np.ndarray
        self.buddy_mean = np.zeros((360, 180, 73))  # type: np.ndarray
        self.buddy_stdev = np.zeros((360, 180, 73))  # type: np.ndarray
        self.nobs = np.zeros((360, 180, 73))  # type: np.ndarray

    @inspect_arrays(["lats", "lons", "dates", "values"])
    def add_multiple_observations(
        self,
        lats: Sequence[float],
        lons: Sequence[float],
        dates: Sequence[datetime],
        values: Sequence[float],
    ) -> None:
        """Add a series of observations to the grid and take the grid average

        Parameters
        ----------
        lats: array-like of float, shape (n,)
            1-dimensional latitude array.
        lons: array-like of float, shape (n,)
            1-dimensional longitude array.
        dates: array-like of datetime, shape (n,)
            1-dimensional date array.
        values: array-like of float, shape (n,)
            1-dimensional anomaly array.
        """
        n_obs = len(lats)
        for i in range(n_obs):
            self.add_single_observation(lats[i], lons[i], dates[i].month, dates[i].day, values[i])
        self.take_average()

    def add_single_observation(self, lat: float, lon: float, month: int, day: int, anom: float) -> None:
        """Add an anomaly to the grid from specified lat lon and date.

        Parameters
        ----------
        lat: float
            Latitude of the observation in degrees
        lon: float
            Longitude of the observation in degrees
        month: int
            Month of the observation
        day: int
            Day of the observation
        anom: float
            Value to be added to the grid

        Returns
        -------
        None
        """
        xindex = mds_lon_to_xindex(lon, res=1.0)
        yindex = mds_lat_to_yindex(lat, res=1.0)
        pindex = which_pentad(month, day) - 1

        assert 0 <= xindex < 360, "bad lon" + str(lon)
        assert 0 <= yindex < 180, "bad lat" + str(lat)
        assert 0 <= pindex < 73, "bad pentad" + str(month) + str(day)

        if anom is not None:
            self.grid[xindex][yindex][pindex] += anom
            self.nobs[xindex][yindex][pindex] += 1

    def take_average(self) -> None:
        """Take the average of a grid to which reps have been added using add_rep"""
        nonmiss = np.nonzero(self.nobs)
        self.grid[nonmiss] = self.grid[nonmiss] / self.nobs[nonmiss]

    def get_neighbour_anomalies(
        self,
        search_radius: list,
        xindex: int,
        yindex: int,
        pindex: int
    ) -> (list[float], list[float]):
        """Search within a specified search radius of the given point and extract the neighbours for buddy check

        Parameters
        ----------
        search_radius: list
            three element array search radius in which to look lon, lat, time
        xindex: int
            the xindex of the gridcell to start from
        yindex: int
            the yindex of the gridcell to start from
        pindex: int
            the pindex of the gridcell to start from

        Returns
        -------
        list[float]
            anomalies and numbers of observations in two lists
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

        for xpt, ypt, ppt in itertools.product(
            range(-1 * full_xspan, full_xspan + 1),
            range(-1 * yspan, yspan + 1),
            range(-1 * pspan, pspan + 1),
        ):
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
        self,
        pentad_stdev: Climatology,
        limits: list[int],
        number_of_obs_thresholds: list[int],
        multipliers: list[float],
    ) -> None:
        """Get buddy limits with parameters.

        Parameters
        ----------
        pentad_stdev: Climatology
            Climatology object containing the 3-dimensional latitude array containing the standard deviations
        limits: list[int]
            list of the limits
        number_of_obs_thresholds: list[int]
            list containing the number of obs thresholds
        multipliers: list[float]
            list containing the multipliers to be applied

        Returns
        -------
        None
        """
        nonmiss = np.nonzero(self.nobs)
        for i in range(len(nonmiss[0])):
            xindex = nonmiss[0][i]
            yindex = nonmiss[1][i]
            pindex = nonmiss[2][i]
            m, d = pentad_to_month_day(pindex + 1)

            stdev = pentad_stdev.get_value_mds_style(89.5 - yindex, -179.5 + xindex, m, d)

            if stdev is None or stdev < 0.0:
                stdev = 1.0

            match_not_found = True

            for j, limit in enumerate(limits):
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    limit, xindex, yindex, pindex
                )

                if len(temp_anom) > 0 and match_not_found:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = int(np.sum(temp_nobs))

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

    def get_new_buddy_limits(
        self,
        stdev1: Climatology,
        stdev2: Climatology,
        stdev3: Climatology,
        limits: list[int, int, int] = (2, 2, 4),
        sigma_m: float = 1.0,
        noise_scaling: float = 3.0,
    ) -> None:
        """Get buddy limits for new bayesian buddy check.

        Parameters
        ----------
        stdev1: np.ndarray
            Field of standard deviations representing standard deviation of difference between target
            gridcell and complete neighbour average (grid area to neighbourhood difference)
        stdev2: np.ndarray
            Field of standard deviations representing standard deviation of difference between a single
            observation and the target gridcell average (point to grid area difference)
        stdev3: np.ndarray
            Field of standard deviations representing standard deviation of difference between random
            neighbour gridcell and full neighbour average (uncertainty in neighbour average)
        limits: list[float]
            three membered list of number of degrees in latitude and longitude and number of pentads
        sigma_m: float
            Estimated measurement error uncertainty
        noise_scaling: float
            scale noise by a factor of noise_scaling used to match observed variability

        Returns
        -------
        None
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

    def get_buddy_mean(self, lat: float, lon: float, month: int, day: int) -> float:
        """Get the buddy mean from the grid for a specified time and place

        Parameters
        ----------
        lat: float
            latitude of the location for which the buddy mean is desired
        lon: float
            longitude of the location for which the buddy mean is desired
        month: int
            month for which the buddy mean is desired
        day: int
            day for which the buddy mean is desired

        Returns
        -------
        float
            Buddy mean at the specified location
        """
        xindex = mds_lon_to_xindex(lon, res=1.0)
        yindex = mds_lat_to_yindex(lat, res=1.0)
        pindex = which_pentad(month, day) - 1
        return self.buddy_mean[xindex][yindex][pindex]

    def get_buddy_stdev(self, lat: float, lon: float, month: int, day: int) -> float:
        """Get the buddy standard deviation from the grid for a specified time and place

        Parameters
        ----------
        lat: float
            latitude of the location for which the buddy standard deviation is desired
        lon: float
            longitude of the location for which the buddy standard deviation is desired
        month: int
            month for which the buddy standard deviation is desired
        day: int
            day for which the buddy standard deviation is desired

        Returns
        -------
        float
            Buddy standard deviation at the specified location
        """
        xindex = mds_lon_to_xindex(lon, res=1.0)
        yindex = mds_lat_to_yindex(lat, res=1.0)
        pindex = which_pentad(month, day) - 1
        return self.buddy_stdev[xindex][yindex][pindex]


@inspect_arrays(["lats", "lons", "dates", "anoms"])
def mds_buddy_check(
        lats: Sequence[float],
        lons: Sequence[float],
        dates: Sequence[datetime],
        anoms: Sequence[float],
        pentad_stdev: Climatology,
        parameters: dict
):
    """Do the old style buddy check.

    Parameters
    ----------
    lats: array-like of float, shape (n,)
        1-dimensional latitude array.
    lons: array-like of float, shape (n,)
        1-dimensional longitude array.
    dates: array-like of datetime, shape (n,)
        1-dimensional date array.
    anoms: array-like of float, shape (n,)
        1-dimensional anomaly array.
    pentad_stdev: Climatology
        Field of standard deviations of 1x1xpentad standard deviations
    parameters: dict
        Dictionary of parameters for the buddy check

    Returns
    -------
    array-like of int, shape (n,)
        1-dimensional array containing QC flags.
        1 if buddy check fails, 0 otherwise.
    """
    limits = parameters["limits"]
    number_of_obs_thresholds = parameters["number_of_obs_thresholds"]
    multipliers = parameters["multipliers"]

    # calculate superob averages and numbers of observations
    grid = SuperObsGrid()
    grid.add_multiple_observations(lats, lons, dates, anoms)
    grid.get_buddy_limits_with_parameters(
        pentad_stdev, limits, number_of_obs_thresholds, multipliers
    )

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


@inspect_arrays(["lats", "lons", "dates", "anoms"])
def bayesian_buddy_check(
    lats: Sequence[float],
    lons: Sequence[float],
    dates: Sequence[datetime],
    anoms: Sequence[float],
    stdev1: clim.Climatology,
    stdev2: clim.Climatology,
    stdev3: clim.Climatology,
) -> Sequence[int]:
    """Do the Bayesian buddy check. The bayesian buddy check assigns a
    probability of gross error to each observation, which is rounded down to the
    tenth and then multiplied by 10 to yield a flag between 0 and 9.

    Parameters
    ----------
    lats: array-like of float, shape (n,)
        1-dimensional latitude array.
    lons: array-like of float, shape (n,)
        1-dimensional longitude array.
    dates: array-like of datetime, shape (n,)
        1-dimensional date array.
    anoms: array-like of float, shape (n,)
        1-dimensional anomaly array.
    stdev1: clim.Climatology
        Field of standard deviations representing standard deviation of difference between
        target gridcell and complete neighbour average (grid area to neighbourhood difference)
    stdev2: clim.Climatology
        Field of standard deviations representing standard deviation of difference between
        a single observation and the target gridcell average (point to grid area difference)
    stdev3: clim.Climatology
        Field of standard deviations representing standard deviation of difference between
        random neighbour gridcell and full neighbour average (uncertainty in neighbour average)

    Returns
    -------
    array-like of int, shape (n,)
        1-dimensional array containing probability of gross error
    """
    parameters = {
        "bayesian_buddy_check": {
            "prior_probability_of_gross_error": 0.05,
            "quantization_interval": 0.1,
            "limits": [2, 2, 4],
            "noise_scaling": 3.0,
            "measurement_error": 1.0,
        },
        "maximum_anomaly": 8.0,
    }

    p0 = parameters["bayesian_buddy_check"]["prior_probability_of_gross_error"]
    q = parameters["bayesian_buddy_check"]["quantization_interval"]
    sigma_m = parameters["bayesian_buddy_check"]["measurement_error"]

    # previous upper QC limits set. Ideally, this should be set based on any previous QC checks.
    # The original default was 8 because the climatology check had a range of +-8C. However, a
    # climatology plus standard deviation check might narrow that range and it might also be
    # spatially varying. There is currently no means of expressing that here.
    r_hi = parameters["maximum_anomaly"]
    r_lo = -1.0 * r_hi  # previous lower QC limit set

    limits = parameters["bayesian_buddy_check"]["limits"]
    noise_scaling = parameters["bayesian_buddy_check"]["noise_scaling"]

    grid = SuperObsGrid()
    grid.add_multiple_observations(lats, lons, dates, anoms)
    grid.get_new_buddy_limits(stdev1, stdev2, stdev3, limits, sigma_m, noise_scaling)

    numobs = len(lats)
    qc_outcomes = np.zeros(numobs) + untested

    for i in range(numobs):
        lat = lats[i]
        lon = lons[i]
        mon = dates[i].month
        day = dates[i].day

        # Calculate the probability of gross error given the set-up
        ppp = p_gross(
            p0,
            q,
            r_hi,
            r_lo,
            anoms[i],
            grid.get_buddy_mean(lat, lon, mon, day),
            grid.get_buddy_stdev(lat, lon, mon, day),
        )

        # QC outcome is coded as an integer between 0 and 9 indicating 10 times the probability of
        # gross error.
        qc_outcomes[i] = 0
        if ppp > 0:
            flag = int(math.floor(ppp * 10))
            flag = min(flag, 9)
            qc_outcomes[i] = flag

    del grid

    return qc_outcomes
