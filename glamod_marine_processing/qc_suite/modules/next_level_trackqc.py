"""Marine QC tracking module."""

# noqa: S101

from __future__ import annotations

import copy
import math
import warnings

import numpy as np

from .qc import passed, failed, untested, untestable
from . import Extended_IMMA as ex
from .astronomical_geometry import sunangle
from .spherical_geometry import sphere_distance
from .time_control import dayinyear

"""
The trackqc module contains a set of functions for performing the tracking QC
first described in Atkinson et al. [2013]. The general procedures described
in Atkinson et al. [2013] were later revised and improved for the SST CCI 2 project.
Documentation and IDL code for the revised (and original) procedures can be found
in the CMA FCM code repository. The code in this module represents a port of the
revised IDL code into the python marine QC suite. New versions of the aground
and speed checks have also been added.

These functions perform tracking QC checks on a :py:class:`ex.Voyage`.

References:

Atkinson, C.P., N.A. Rayner, J. Roberts-Jones, R.O. Smith, 2013:
Assessing the quality of sea surface temperature observations from
drifting buoys and ships on a platform-by-platform basis (doi:10.1002/jgrc.20257).
"""


def track_day_test(
    year: int,
    month: int,
    day: int,
    hour: float,
    lat: float,
    lon: float,
    elevdlim: float = -2.5,
) -> bool:
    """Given date, time, lat and lon calculate if the sun elevation is > elevdlim.
    If so return daytime is True

    This is the "day" test used by tracking QC to decide whether an SST measurement is night or day.
    This is important because daytime diurnal heating can affect comparison with an SST background.
    It uses the function sunangle to calculate the elevation of the sun. A default solar_zenith angle
    of 92.5 degrees (elevation of -2.5 degrees) delimits night from day.

    Parameters
    ----------
    year: int
        Year
    month: int
        Month
    day: int
        Day
    hour: float
        Hour expressed as decimal fraction (e.g. 20.75 = 20:45 pm)
    lat: float
        Latitude in degrees
    lon: float
        Longitude in degrees
    elevdlim: float
        Elevation day/night delimiter in degrees above horizon

    Returns
    -------
    bool
        True if daytime, else False.

    Raises
    ------
    ValueError
        When input values are invalid
    """
    if year is None:
        raise ValueError("year is missing")
    if month is None:
        raise ValueError("month is missing")
    if day is None:
        raise ValueError("day is missing")
    if hour is None:
        raise ValueError("hour is missing")
    if lat is None:
        raise ValueError("lat is missing")
    if lon is None:
        raise ValueError("lon is missing")
    if not (1 <= month <= 12):
        raise ValueError("Month not in range 1-12")
    if not (1 <= day <= 31):
        raise ValueError("Day not in range 1-31")
    if not (0 <= hour <= 24):
        raise ValueError("Hour not in range 0-24")
    if not (90 >= lat >= -90):
        raise ValueError("Latitude not in range -90 to 90")

    daytime = False

    year2 = year
    day2 = dayinyear(year, month, day)
    hour2 = math.floor(hour)
    minute2 = (hour - math.floor(hour)) * 60.0
    lat2 = lat
    lon2 = lon
    if lat == 0:
        lat2 = 0.0001
    if lon == 0:
        lon2 = 0.0001

    _, elevation, _, _, _, _ = sunangle(
        year2, day2, hour2, minute2, 0, 0, 0, lat2, lon2
    )

    if elevation > elevdlim:
        daytime = True

    return daytime


def trim_mean(inarr: list, trim: int) -> float:
    """Calculate a resistant (aka robust) mean of an input array given a trimming criteria.

    Parameters
    ----------
    inarr: list
        Array of numbers
    trim: int
        trimming criteria. A value of 10 trims one tenth of the values off each end of the sorted array
        before calculating the mean.

    Returns
    -------
    float
        Trimmed mean
    """
    arr = np.array(inarr)  # type: np.ndarray
    if trim == 0:
        return float(np.mean(arr))

    length = len(arr)
    arr.sort()

    index1 = int(length / trim)

    trim = float(np.mean(arr[index1 : length - index1]))

    return trim


def trim_std(inarr: list, trim: int) -> float:
    """Calculate a resistant (aka robust) standard deviation of an input array given a trimming criteria.

    Parameters
    ----------
    inarr : list
        Array of numbers
    trim: int
        trimming criteria. A value of 10 trims one tenth of the values off each end of the sorted array before
        calculating the standard deviation.

    Returns
    -------
    float
        Returns trimmed standard deviation
    """
    arr = np.array(inarr)  # type: np.ndarray
    if trim == 0:
        return float(np.std(arr))

    length = len(arr)
    arr.sort()

    index1 = int(length / trim)

    trim = float(np.std(arr[index1 : length - index1]))

    return trim

def convert_date_to_hours(dates):
    hours_elapsed = np.zeros(len(dates))
    for i in range(len(dates)):
        duration_in_seconds = (dates[i] - dates[0]).total_seconds()
        hours_elapsed[i] = duration_in_seconds/(60*60)
    return hours_elapsed


def is_monotonic(inarr: np.ndarray) -> bool:
    """
    Tests if elements in an array are increasing monotonically. i.e. each element
    is greater than or equal to the preceding element.

    Parameters
    ----------
    inarr: np.ndarray

    Returns
    -------
    bool
        True if array is increasing monotonically, False otherwise
    """
    for i in range(1, len(inarr)):
        if inarr[i] < inarr[i-1]:
            return False
    return True


def do_speed_check(lons, lats, dates, speed_limit, min_win_period, max_win_period):
    checker = SpeedChecker(lons, lats, dates, speed_limit, min_win_period, max_win_period)
    checker._do_speed_check()
    return checker.get_qc_outcomes()



class SpeedChecker:
    """Check to see whether a drifter has been picked up by a ship (out of water) based on 1/100th degree
    precision positions. A flag 'drf_spd' is set for each input report: flag=1 for reports deemed picked up,
    else flag=0.

    A drifter is deemed picked up if it is moving faster than might be expected for a fast ocean current
    (a few m/s). Unreasonably fast movement is detected when speed of travel between report-pairs exceeds
    the chosen 'speed_limit' (speed is estimated as distance between reports divided by time separation -
    this 'straight line' speed between the two points is a minimum speed estimate given a less-direct
    path may have been followed). Positional errors introduced by lon/lat 'jitter' and data precision
    can be of order several km's. Reports must be separated by a suitably long period of time (the 'min_win_period')
    to minimise the effect of these errors when calculating speed e.g. for reports separated by 24 hours
    errors of several cm/s would result which are two orders of magnitude less than a fast ocean current
    which seems reasonable. Conversely, the period of time chosen should not be too long so as to resolve
    short-lived burst of speed on manoeuvring ships. Larger positional errors may also trigger the check.
    Because temporal sampling can be erratic the time period over which this assessment is made is specified
    as a range (bound by 'min_win_period' and 'max_win_period') - assessment uses the longest time separation
    available within this range.

    IMPORTANT - for optimal performance, drifter records with observations failing this check should be
    subsequently manually reviewed. Ships move around in all sorts of complicated ways that can readily
    confuse such a simple check (e.g. pausing at sea, crisscrossing its own path) and once some erroneous
    movement is detected it is likely a human operator can then better pick out the actual bad data. False
    fails caused by positional errors (particularly in fast ocean currents) will also need reinstating.

    speed_limit: maximum allowable speed for an in situ drifting buoy (metres per second)
    min_win_period: minimum period of time in days over which position is assessed for speed estimates (see
      description)
    max_win_period: maximum period of time in days over which position is assessed for speed estimates
      (this should be greater than min_win_period and allow for some erratic temporal sampling e.g. min_win_period+0.2
      to allow for gaps of up to 0.2-days in sampling).
    """

    # speed_limit = 2.5
    # min_win_period = 0.8
    # max_win_period = 1.0

    def __init__(self, lons, lats, dates, speed_limit, min_win_period, max_win_period):
        self.good_parameters = True
        self.lon = lons
        self.lat = lats
        self.nreps = len(lons)
        self.hrs = convert_date_to_hours(dates)

        self.speed_limit = speed_limit
        self.min_win_period = min_win_period
        self.max_win_period = max_win_period

        # Initialise QC outcomes with untested
        self.qc_outcomes = np.zeros(self.nreps) + untested

    def get_qc_outcomes(self):
        return self.qc_outcomes

    def valid_parameters(self) -> bool:
        """Check the parameters"""
        valid = True

        try:
            assert self.speed_limit >= 0, "speed_limit must be >= 0"
            assert self.min_win_period >= 0, "min_win_period must be >= 0"
            assert self.max_win_period >= 0, "max_win_period must be >= 0"
            assert (
            self.max_win_period >= self.min_win_period
            ), "max_win_period must be >= min_win_period"
        except AssertionError as error:
            warnings.warn(UserWarning("invalid input parameter: " + str(error)))
            valid = False

        return valid

    def valid_arrays(self) -> bool:
        valid = True
        if any(np.isnan(self.lon)):
            warnings.warn(UserWarning("Nan(s) found in longitude"))
            valid = False
        if any(np.isnan(self.lat)):
            warnings.warn(UserWarning("Nan(s) found in latitude"))
            valid = False
        if any(np.isnan(self.hrs)):
            warnings.warn(UserWarning("Nan(s) found in time differences"))
            valid = False
        if not(is_monotonic(self.hrs)):
            warnings.warn(UserWarning("times are not sorted"))
            valid = False
        return valid

    def _do_speed_check(self):
        """Perform the actual speed check"""
        nrep = self.nreps
        min_win_period_hours = self.min_win_period * 24.0
        max_win_period_hours = self.max_win_period * 24.0

        if not self.valid_arrays() or not self.valid_parameters():
            self.qc_outcomes = np.zeros(self.nreps) + untestable
            return

        # Initialise
        self.qc_outcomes = np.zeros(nrep) + passed

        # loop through timeseries to see if drifter is moving too fast
        # and flag any occurrences
        index_arr = np.array(range(0, nrep)) # type: np.ndarray
        i = 0
        time_to_end = self.hrs[-1] - self.hrs[i]
        while time_to_end >= min_win_period_hours:
            # Find all time points before current time plus the max window period
            f_win = self.hrs <= self.hrs[i] + max_win_period_hours
            # Window length is the difference between the latest time point in
            # the window and the current time
            win_len = self.hrs[f_win][-1] - self.hrs[i]
            # If the actual window length is shorter than the minimum window period
            # then go to the next time step
            if win_len < min_win_period_hours:
                i += 1
                time_to_end = self.hrs[-1] - self.hrs[i]
                continue

            # If the actual window length is long enough then calculate the speed
            # based on the first and last points in the window
            displace = sphere_distance(
                self.lat[i], self.lon[i], self.lat[f_win][-1], self.lon[f_win][-1]
            )
            speed = displace / win_len  # km per hr
            speed = speed * 1000.0 / (60.0 * 60)  # metres per sec

            # If the average speed during the window is too high then set all
            # flags in the window to failed.
            if speed > self.speed_limit:
                self.qc_outcomes[i:index_arr[f_win][-1] + 1] = failed

            i += 1
            time_to_end = self.hrs[-1] - self.hrs[i]

        return

