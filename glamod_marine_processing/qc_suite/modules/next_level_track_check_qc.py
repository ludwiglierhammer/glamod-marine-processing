"""Module containing QC functions for track checking which could be applied on a DataBundle."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

import numpy as np
import pandas as pd

import glamod_marine_processing.qc_suite.modules.icoads_identify as icoads_identify
import glamod_marine_processing.qc_suite.modules.spherical_geometry as sg
import glamod_marine_processing.qc_suite.modules.time_control as time_control
import glamod_marine_processing.qc_suite.modules.track_check as tc
from glamod_marine_processing.qc_suite.modules.qc import failed, passed

km_to_nm = 0.539957


def do_spike_check(
    sst: Sequence[float],
    lat: Sequence[float],
    lon: Sequence[float],
    date: Sequence[datetime],
    delta_t: float = 2.0,
) -> Sequence[int]:
    """Perform IQUAM like spike check.

    Parameters
    ----------
    sst: array-like of float, shape (n,)
        1-dimensional sea surface temperature array.
    lat: array-like of float, shape (n,)
        1-dimensional latitude array in degrees.
    lon: array-like of float, shape (n,)
        1-dimensional longitude array in degrees.
    date: array-like of datetime, shape (n,)
        1-dimensional date array.
    delta_t: float, default 2.0
        ???
        This should be 2.0 for ships and 1.0 for drifting buoys.

    Returns
    -------
    array-like of int, shape (n,)
        1- dimensional array containing QC flags.
        1 if spike check fails, 0 otherwise.

    Raises
    ------
    ValueError
        If either input is not 1-dimensional or if their lengths do not match.
    """
    sst = np.asarray(sst)
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    date = np.asarray(date)

    for arr, name in zip([sst, lat, lon, date], ["sst", "lat", "lon", "date"]):
        if arr.ndim != 1:
            raise ValueError(f"Input '{name}' must be one-dimensional.")
        if len(arr) != len(sst):
            raise ValueError(f"Input '{name}' must have the same length as 'sst'.")

    max_gradient_space = 0.5  # K/km
    max_gradient_time = 1.0  # K/hr

    n_neighbours = 5

    gradient_violations = []
    count_gradient_violations = []

    number_of_obs = len(sst)

    spike_qc = np.asarray([passed] * number_of_obs)

    for t1 in range(number_of_obs):

        violations_for_this_report = []
        count_violations_this_report = 0.0

        lo = max(0, t1 - n_neighbours)
        hi = min(number_of_obs, t1 + n_neighbours + 1)

        for t2 in range(lo, hi):

            if sst[t1] is None or sst[t2] is None:
                continue

            distance = sg.sphere_distance(lat[t1], lon[t1], lat[t2], lon[t2])
            delta = pd.Timestamp(date[t2]) - pd.Timestamp(date[t2])
            time_diff = abs(delta.days * 24 + delta.seconds / 3600.0)
            val_change = abs(sst[t2] - sst[t1])

            iquam_condition = max(
                [
                    delta_t,
                    abs(distance) * max_gradient_space,
                    abs(time_diff) * max_gradient_time,
                ]
            )

            if val_change > iquam_condition:
                violations_for_this_report.append(t2)
                count_violations_this_report += 1.0

        gradient_violations.append(violations_for_this_report)
        count_gradient_violations.append(count_violations_this_report)

    while np.sum(count_gradient_violations) > 0.0:
        most_fails = int(np.argmax(count_gradient_violations))
        spike_qc[most_fails] = failed

        for index in gradient_violations[most_fails]:
            if most_fails in gradient_violations[index]:
                gradient_violations[index].remove(most_fails)
                count_gradient_violations[index] -= 1.0

        count_gradient_violations[most_fails] = 0

    return spike_qc


def calculate_course_parameters(
    lat_later: float,
    lat_earlier: float,
    lon_later: float,
    lon_earlier: float,
    date_later: datetime,
    date_earlier: datetime,
) -> tuple[float, float, float, float]:
    """Calculate course parameters.

    Parameters
    ----------
    lat_later: float
        Latitude in degrees of later timestamp.
    lat_earlier:float
        Latitude in degrees of earlier timestamp.
    lon_later: float
        Longitude in degrees of later timestamp.
    lon_earlier: float
        Longitude in degrees of earlier timestamp.
    date_later: datetime
        Date of later timestamp.
    date_earlier: datetime
        Date of earlier timestamp.

    Returns
    -------
    tuple of float
        A tuple of four floats representing the speed, distance, course and time difference
    """
    distance = sg.sphere_distance(lat_later, lon_later, lat_earlier, lon_earlier)
    date_earlier = pd.Timestamp(date_earlier)
    date_later = pd.Timestamp(date_later)

    timediff = time_control.time_difference(
        date_earlier.year,
        date_earlier.month,
        date_earlier.day,
        date_earlier.hour,
        date_later.year,
        date_later.month,
        date_later.day,
        date_later.hour,
    )
    if timediff != 0 and timediff is not None:
        speed = distance / abs(timediff)
    else:
        timediff = 0.0
        speed = distance

    course = sg.course_between_points(lat_earlier, lon_earlier, lat_later, lon_later)

    return speed, distance, course, timediff


def calculate_speed_course_distance_time_difference(
    lat: Sequence[float],
    lon: Sequence[float],
    date: Sequence[datetime],
    alternating: bool = False,
) -> tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[float]]:
    """
    Calculates speeds, courses, distances and time differences using consecutive reports.

    Parameters
    ----------
    lat: array-like of float, shape (n,)
        1-dimensional latitude array in degrees.
    lon: array-like of float, shape (n,)
        1-dimensional longitude array in degrees.
    date: array-like of datetime, shape (n,)
        1-dimensional date array.
    alternating: bool, default: False
        Use alternating reports for calculation

    Returns
    -------
    tuple of array-like of float, shape (n,)
        A tuple of four 1-dimensional arrays of floats representing speed, distance, course and time difference.

    Raises
    ------
    ValueError
        If either input is not 1-dimensional or if their lengths do not match.
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    date = np.asarray(date)

    for arr, name in zip([lat, lon, date], ["lat", "lon", "date"]):
        if arr.ndim != 1:
            raise ValueError(f"Input '{name}' must be one-dimensional.")
        if len(arr) != len(lat):
            raise ValueError(f"Input '{name}' must have the same length as 'lat'.")

    number_of_obs = len(lat)

    speed = np.empty(number_of_obs)  # type: np.ndarray
    course = np.empty(number_of_obs)  # type: np.ndarray
    distance = np.empty(number_of_obs)  # type: np.ndarray
    timediff = np.empty(number_of_obs)  # type: np.ndarray

    speed.fill(np.nan)
    course.fill(np.nan)
    distance.fill(np.nan)
    timediff.fill(np.nan)

    if number_of_obs == 1:
        return speed, distance, course, timediff

    range_end = number_of_obs
    first_entry = "i"
    second_entry = "i - 1"
    if alternating is True:
        range_end = number_of_obs - 1
        first_entry = "i + 1"
        second_entry = "i - 1"

    for i in range(1, range_end):
        fe = eval(first_entry)
        se = eval(second_entry)
        ship_speed, ship_distance, ship_direction, ship_time_difference = (
            calculate_course_parameters(
                lat[fe], lat[se], lon[fe], lon[se], date[fe], date[se]
            )
        )

        speed[i] = ship_speed
        course[i] = ship_direction
        distance[i] = ship_distance
        timediff[i] = ship_time_difference

    return speed, distance, course, timediff


def forward_discrepancy(
    lat: Sequence[float],
    lon: Sequence[float],
    date: Sequence[datetime],
    speed: Sequence[float],
    direction: Sequence[float],
) -> Sequence[float]:
    """Calculate what the distance is between the projected position (based on the reported
    speed and heading at the current and previous time steps) and the actual position. The
    observations are taken in time order.

    This takes the speed and direction reported by the ship and projects it forwards half a
    time step, it then projects it forwards another half time-step using the speed and
    direction for the next report, to which the projected location
    is then compared. The distances between the projected and actual locations is returned

    Parameters
    ----------
    lat: array-like of float, shape (n,)
        1-dimensional latitude array in degrees.
    lon: array-like of float, shape (n,)
        1-dimensional longitude array in degrees.
    date: array-like of datetime, shape (n,)
        1-dimensional date array.
    speed: array-like of float, shape (n,)
        1-dimensional speed array in kilometer per hour.
    direction: array-like of float, shape (n,)
        1-dimensional direction array.

    Returns
    -------
    array-like of float, shape (n,)
        1-dimensional array containing distances from estimated positions.

    Raises
    ------
    ValueError
        If either input is not 1-dimensional or if their lengths do not match.
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    date = np.asarray(date)
    speed = np.asarray(speed) / km_to_nm
    direction = np.asarray(direction)

    for arr, name in zip(
        [lat, lon, date, speed, direction], ["lat", "lon", "date", "speed", "direction"]
    ):
        if arr.ndim != 1:
            raise ValueError(f"Input '{name}' must be one-dimensional.")
        if len(arr) != len(lat):
            raise ValueError(f"Input '{name}' must have the same length as 'lat'.")

    number_of_obs = len(lat)

    distance_from_est_location = np.asarray([np.nan] * number_of_obs)

    for i in range(1, number_of_obs):

        vsi = speed[i]
        vsi_minus_one = speed[i - 1]
        dsi = direction[i]
        dsi_minus_one = direction[i - 1]
        tsi = pd.Timestamp(date[i])
        tsi_minus_one = pd.Timestamp(date[i - 1])
        lai = lat[i]
        lai_minus_one = lat[i - 1]
        loi = lon[i]
        loi_minus_one = lon[i - 1]

        if (
            vsi is None
            or vsi_minus_one is None
            or dsi is None
            or dsi_minus_one is None
            or tsi is None
            or tsi_minus_one is None
            or lai is None
            or lai_minus_one is None
            or loi is None
            or loi_minus_one is None
        ):
            continue

        time_diff = tsi - tsi_minus_one
        # get increment from initial position
        lat1, lon1 = tc.increment_position(
            lai_minus_one,
            loi_minus_one,
            vsi_minus_one,
            dsi_minus_one,
            time_diff,
        )

        lat2, lon2 = tc.increment_position(
            lai,
            loi,
            vsi,
            dsi,
            time_diff,
        )

        # apply increments to the lat and lon at i-1
        updated_latitude = lai_minus_one + lat1 + lat2
        updated_longitude = loi_minus_one + lon1 + lon2

        # calculate distance between calculated position and the second reported position
        discrepancy = sg.sphere_distance(lai, loi, updated_latitude, updated_longitude)

        distance_from_est_location[i] = discrepancy

    return distance_from_est_location


def backward_discrepancy(
    lat: Sequence[float],
    lon: Sequence[float],
    date: Sequence[datetime],
    speed: Sequence[float],
    direction: Sequence[float],
) -> Sequence[float]:
    """Calculate what the distance is between the projected position (based on the reported speed and
    heading at the current and previous time steps) and the actual position. The calculation proceeds from the
    final, later observation to the first (in contrast to distr1 which runs in time order)

    This takes the speed and direction reported by the ship and projects it forwards half a time step, it then
    projects it forwards another half time step using the speed and direction for the next report, to which the
    projected location is then compared. The distances between the projected and actual locations is returned

    Parameters
    ----------
    lat: array-like of float, shape (n,)
        1-dimensional latitude array in degrees.
    lon: array-like of float, shape (n,)
        1-dimensional longitude array in degrees.
    date: array-like of datetime, shape (n,)
        1-dimensional date array.
    speed: array-like of float, shape (n,)
        1-dimensional speed array in kilometer per hour.
    direction: array-like of float, shape (n,)
        1-dimensional direction array.

    Returns
    -------
    array-like of float, shape (n,)
        1-dimensional array containing distances from estimated positions.

    Raises
    ------
    ValueError
        If either input is not 1-dimensional or if their lengths do not match.
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    date = np.asarray(date)
    speed = np.asarray(speed) / km_to_nm
    direction = np.asarray(direction) - 180.0

    for arr, name in zip(
        [lat, lon, date, speed, direction], ["lat", "lon", "date", "speed", "direction"]
    ):
        if arr.ndim != 1:
            raise ValueError(f"Input '{name}' must be one-dimensional.")
        if len(arr) != len(lat):
            raise ValueError(f"Input '{name}' must have the same length as 'lat'.")

    number_of_obs = len(lat)

    distance_from_est_location = np.asarray([np.nan] * number_of_obs)

    for i in range(number_of_obs - 1, 0, -1):

        vsi = speed[i]
        vsi_minus_one = speed[i - 1]
        dsi = direction[i]
        dsi_minus_one = direction[i - 1]
        tsi = pd.Timestamp(date[i])
        tsi_minus_one = pd.Timestamp(date[i - 1])
        lai = lat[i]
        lai_minus_one = lat[i - 1]
        loi = lon[i]
        loi_minus_one = lon[i - 1]

        if (
            vsi is None
            or vsi_minus_one is None
            or dsi is None
            or dsi_minus_one is None
            or tsi is None
            or tsi_minus_one is None
            or lai is None
            or lai_minus_one is None
            or loi is None
            or loi_minus_one is None
        ):
            continue

        time_diff = tsi - tsi_minus_one
        # get increment from initial position - backwards in time
        # means reversing the direction by 180 degrees
        lat1, lon1 = tc.increment_position(
            lai,
            loi,
            vsi,
            dsi,
            time_diff,
        )

        lat2, lon2 = tc.increment_position(
            lai_minus_one,
            loi_minus_one,
            vsi_minus_one,
            dsi_minus_one,
            time_diff,
        )

        # apply increments to the lat and lon at i-1
        updated_latitude = lai + lat1 + lat2
        updated_longitude = loi + lon1 + lon2

        # calculate distance between calculated position and the second reported position
        discrepancy = sg.sphere_distance(
            lai_minus_one, loi_minus_one, updated_latitude, updated_longitude
        )
        distance_from_est_location[i] = discrepancy

    # that fancy bit at the end reverses the array
    return distance_from_est_location[::-1]


def calculate_midpoint(
    lat: Sequence[float],
    lon: Sequence[float],
    timediff: Sequence[pd.Timestamp],
) -> Sequence[float]:
    """Interpolate between alternate reports and compare the interpolated location to the actual location. e.g.
    take difference between reports 2 and 4 and interpolate to get an estimate for the position at the time
    of report 3. Then compare the estimated and actual positions at the time of report 3.

    The calculation linearly interpolates the latitudes and longitudes (allowing for wrapping around the
    dateline and so on).

    Parameters
    ----------
    lat: array-like of float, shape (n,)
        1-dimensional latitude array in degrees.
    lon: array-like of float, shape (n,)
        1-dimensional longitude array in degrees.
    time_diff: array-like of datetime, shape (n,)
        1-dimensional time difference array.

    Returns
    -------
    array-like of float, shape (n,)
        1-dimensional array containing distances from estimated positions in km

    Raises
    ------
    ValueError
        If either input is not 1-dimensional or if their lengths do not match.
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    timediff = np.asarray(timediff)

    for arr, name in zip([lat, lon, timediff], ["lat", "lon", "timediff"]):
        if arr.ndim != 1:
            raise ValueError(f"Input '{name}' must be one-dimensional.")
        if len(arr) != len(lat):
            raise ValueError(f"Input '{name}' must have the same length as 'lat'.")

    number_of_obs = len(lat)

    midpoint_discrepancies = np.asarray([np.nan] * number_of_obs)

    for i in range(1, number_of_obs - 1):
        t0 = timediff[i]
        t1 = timediff[i + 1]

        if t0 is not None and t1 is not None:
            if t0 + t1 != 0:
                fraction_of_time_diff = t0 / (t0 + t1)
            else:
                fraction_of_time_diff = 0.0
        else:
            fraction_of_time_diff = 0.0

        estimated_lat_at_midpoint, estimated_lon_at_midpoint = sg.intermediate_point(
            lat[i - 1],
            lon[i - 1],
            lat[i + 1],
            lon[i + 1],
            fraction_of_time_diff,
        )

        discrepancy = sg.sphere_distance(
            lat[i],
            lon[i],
            estimated_lat_at_midpoint,
            estimated_lon_at_midpoint,
        )

        midpoint_discrepancies[i] = discrepancy

    midpoint_discrepancies[i + 1] = np.nan

    return midpoint_discrepancies


def track_check(df: pd.DataFrame) -> pd.DataFrame:
    """Perform one pass of the track check.  This is an implementation of the MDS track check code
    which was originally written in the 1990s. I don't know why this piece of historic trivia so exercises
    my mind, but it does: the 1990s! I wish my code would last so long.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data to be checked

    Returns
    -------
    pd.DataFrame
        DataFrame with track check QC
    """
    required_columns = ["id", "date", "pt", "dck", "dsi", "vsi", "lat", "lon"]

    for key in required_columns:
        if key not in df:
            raise KeyError(f"{key} not in DataFrame")

    max_direction_change = 60.0
    max_speed_change = 10.0
    max_absolute_speed = 40.0
    max_midpoint_discrepancy = 150.0

    nobs = len(df)

    # no obs in, no qc outcomes out
    if nobs == 0:
        return df

    # Generic ids and buoys get a free pass on the track check
    if icoads_identify.id_is_generic(df.iloc[0].id, df.iloc[0].date.year) or df.iloc[
        0
    ].pt in [6, 7]:
        for i in range(0, nobs):
            df["trk"] = np.zeros(nobs)
            df["few"] = np.zeros(nobs)
        return df

    # fewer than three obs - set the fewsome flag
    # deck 720 gets a pass prior to 1891 see
    # Carella, Kent, Berry 2015 Appendix A3
    if nobs < 3:
        if df.iloc[0].dck == 720 and df.iloc[0].date.year < 1891:
            df["trk"] = np.zeros(nobs)
            df["few"] = np.zeros(nobs)
            return df
        else:
            df["trk"] = np.zeros(nobs)
            df["few"] = np.zeros(nobs) + 1
            return df

    # work out speeds and distances between alternating points
    speed_alt, distance_alt, course_alt, timediff_alt = (
        calculate_speed_course_distance_time_difference(
            lat=df.lat,
            lon=df.lon,
            date=df.date,
            alternating=True,
        )
    )
    speed, distance, course, timediff = calculate_speed_course_distance_time_difference(
        lat=df.lat,
        lon=df.lon,
        date=df.date,
    )

    # what are the mean and mode speeds?
    modal_speed = tc.modesp(speed)

    # set speed limits based on modal speed
    amax, _amaxx, _amin = tc.set_speed_limits(modal_speed)

    # compare reported speeds and positions if we have them
    forward_diff_from_estimated = forward_discrepancy(
        lat=df.lat,
        lon=df.lon,
        date=df.date,
        speed=speed,
        direction=direction,
    )
    reverse_diff_from_estimated = backward_discrepancy(
        lat=df.lat,
        lon=df.lon,
        date=df.date,
        speed=speed,
        direction=direction,
    )

    midpoint_diff_from_estimated = calculate_midpoint(
        lat=df.lat,
        lon=df.lon,
        timediff=timediff,
    )

    # do QC
    trk = np.zeros(nobs)  # type: np.ndarray
    few = np.zeros(nobs)  # type: np.ndarray

    for i in range(1, nobs - 1):
        thisqc_a = 0
        thisqc_b = 0

        # together these cover the speeds calculate from point i
        if (
            speed[i] is not None
            and speed[i] > amax
            and speed_alt[i - 1] is not None
            and speed_alt[i - 1] > amax
        ):
            thisqc_a += 1.00
        elif (
            speed[i + 1] is not None
            and speed[i + 1] > amax
            and speed_alt[i + 1] is not None
            and speed_alt[i + 1] > amax
        ):
            thisqc_a += 2.00
        elif (
            speed[i] is not None
            and speed[i] > amax
            and speed[i + 1] is not None
            and speed[i + 1] > amax
        ):
            thisqc_a += 3.00

        # Quality-control by examining the distance
        # between the calculated and reported second position.
        thisqc_b += tc.check_distance_from_estimate(
            df.iloc[i].vsi,
            df.iloc[i - 1].vsi,
            timediff[i],
            forward_diff_from_estimated[i],
            reverse_diff_from_estimated[i],
        )
        # Check for continuity of direction
        thisqc_b += tc.direction_continuity(
            df.iloc[i].dsi,
            df.iloc[i - 1].dsi,
            course[i],
            max_direction_change,
        )
        # Check for continuity of speed.
        thisqc_b += tc.speed_continuity(
            df.iloc[i].vsi,
            df.iloc[i - 1].vsi,
            speed[i],
            max_speed_change,
        )

        # check for speeds in excess of 40.00 knots
        if speed[i] > max_absolute_speed / km_to_nm:
            thisqc_b += 10.0

        # make the final decision
        if (
            midpoint_diff_from_estimated[i] > max_midpoint_discrepancy / km_to_nm
            and thisqc_a > 0
            and thisqc_b > 0
        ):
            trk[i] = 1

    trk[nobs - 1] = 0
    few[nobs - 1] = 0

    return trk, few


def find_saturated_runs(df: pd.DataFrame) -> pd.DataFrame:
    """Perform checks on persistence of 100% rh while going through the voyage.
    While going through the voyage repeated strings of 100 %rh (AT == DPT) are noted.
    If a string extends beyond 20 reports and two days/48 hrs in time then all values are set to
    fail the repsat qc flag.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to be checked

    Returns
    -------
    pd.DataFrame
    """
    for key in ["dpt", "at", "date"]:
        if key not in df:
            raise KeyError(f"{key} not in dataframe")

    min_time_threshold = 48.0  # hours
    shortest_run = 4  # number of obs

    satcount = []

    numobs = len(df)

    repsat = np.zeros(numobs)  # type: np.ndarray

    for i in range(numobs):

        row = df.iloc[i]

        saturated = row["dpt"] == row["at"]

        if saturated:
            satcount.append(i)
        elif not saturated and len(satcount) > shortest_run:

            row2 = df.iloc[satcount[len(satcount) - 1]]
            row1 = df.iloc[satcount[0]]
            _, _, _, tdiff = calculate_course_parameters(row2, row1)

            if tdiff >= min_time_threshold:
                for loc in satcount:
                    repsat[loc] = 1
                satcount = []
            else:
                satcount = []

        else:
            satcount = []

    if len(satcount) > shortest_run:
        row2 = df.iloc[satcount[len(satcount) - 1]]
        row1 = df.iloc[satcount[0]]
        _, _, _, tdiff = calculate_course_parameters(row2, row1)

        if tdiff >= min_time_threshold:
            for loc in satcount:
                repsat[loc] = 1

    df["repsat"] = repsat

    return df


def find_multiple_rounded_values(df: pd.DataFrame, intype: str) -> pd.DataFrame:
    """Find instances when more than "threshold" of the observations are
    whole numbers and set the 'round' flag. Used in the humidity QC
    where there are times when the values are rounded and this may
    have caused a bias.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing data to be checked
    intype: str
        Specifies which variable should be quality controlled

    Returns
    -------
    pd.DataFrame
        Returns dataframe with additional column "rounded" containing QC outcomes
    """
    allowed_variables = ["sst", "at", "dpt"]
    if intype not in allowed_variables:
        raise ValueError(f"{intype} not one of {allowed_variables}")

    min_count = 20
    threshold = 0.5

    assert 0.0 <= threshold <= 1.0

    numobs = len(df)
    rounded = np.zeros(numobs)  # type: np.ndarray

    valcount = {}
    allcount = 0

    for i in range(numobs):
        row = df.iloc[i]
        if row[intype] is not None:
            allcount += 1
            if str(row[intype]) in valcount:
                valcount[str(row[intype])].append(i)
            else:
                valcount[str(row[intype])] = [i]

    if allcount > min_count:
        wholenums = 0
        for key in valcount:
            if float(key).is_integer():
                wholenums = wholenums + len(valcount[key])

        if float(wholenums) / float(allcount) >= threshold:
            for key in valcount:
                if float(key).is_integer():
                    for i in valcount[key]:
                        rounded[i] = 1

    df["rounded"] = rounded

    return df


def find_repeated_values(df: pd.DataFrame, intype: str) -> pd.DataFrame:
    """Find cases where more than a given proportion of SSTs have the same value

    This function goes through a voyage and finds any cases where more than a threshold fraction of
    the observations have the same values for a specified variable.


    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing data to be checked
    intype: str
        Specifies which variable should be quality controlled

    Returns
    -------
    pd.DataFrame
        Returns dataframe with additional column "rep" containing QC outcomes
    """
    allowed_variables = ["sst", "at", "dpt", "slp"]
    if intype not in allowed_variables:
        raise ValueError(f"{intype} not one of {allowed_variables}")

    threshold = 0.7
    assert 0.0 <= threshold <= 1.0
    min_count = 20

    numobs = len(df)
    rep = np.zeros(numobs)  # type: np.ndarray

    valcount = {}
    allcount = 0

    for i in range(numobs):
        row = df.iloc[i]
        value = row[intype]
        if value is not None:
            allcount += 1
            if str(value) in valcount:
                valcount[str(value)].append(i)
            else:
                valcount[str(value)] = [i]

    if allcount > min_count:
        for key in valcount:
            if float(len(valcount[key])) / float(allcount) > threshold:
                for i in valcount[key]:
                    rep[i] = 1

    df["rep"] = rep

    return df


def iquam_track_check(df: pd.DataFrame) -> pd.DataFrame:
    """Perform the IQUAM track check as detailed in Xu and Ignatov 2013

    The track check calculates speeds between pairs of observations and
    counts how many exceed a threshold speed. The ob with the most
    violations of this limit is flagged as bad and removed from the
    calculation. Then the next worst is found and removed until no
    violatios remain.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing data to be track checked.

    Returns
    -------
    pd.DataFrame
        Returns DataFrame with additional column "iquam_track" containing the outcomes of the QC
    """
    for key in ["lat", "lon", "id", "date"]:
        if key not in df:
            raise KeyError(f"{key} not in dataframe")

    buoy_speed_limit = 15.0  # km/h
    ship_speed_limit = 60.0  # km/h

    delta_d = 1.11  # 0.1 degrees of latitude
    delta_t = 0.01  # one hundredth of an hour

    n_neighbours = 5

    numobs = len(df)

    if numobs == 0:
        return df

    if icoads_identify.id_is_generic(df.iloc[0].id, df.iloc[0].date.year):
        df["iquam_track"] = np.zeros(numobs)
        return df

    if df.iloc[0].pt in [6, 7]:
        speed_limit = buoy_speed_limit
    else:
        speed_limit = ship_speed_limit

    speed_violations = []
    count_speed_violations = []

    iquam_track = np.zeros(numobs)  # type: np.ndarray

    for t1 in range(0, numobs):
        violations_for_this_report = []
        count_violations_this_report = 0.0

        lo = max(0, t1 - n_neighbours)
        hi = min(numobs, t1 + n_neighbours + 1)

        for t2 in range(lo, hi):

            row2 = df.iloc[t2]
            row1 = df.iloc[t1]

            _, distance, _, time_diff = calculate_course_parameters(row2, row1)

            iquam_condition = max([abs(distance) - delta_d, 0.0]) / (
                abs(time_diff) + delta_t
            )

            if iquam_condition > speed_limit:
                violations_for_this_report.append(t2)
                count_violations_this_report += 1.0

        speed_violations.append(violations_for_this_report)
        count_speed_violations.append(count_violations_this_report)

    count = 0
    while np.sum(count_speed_violations) > 0.0:
        most_fails = int(np.argmax(count_speed_violations))
        iquam_track[most_fails] = 1

        for index in speed_violations[most_fails]:
            if most_fails in speed_violations[index]:
                speed_violations[index].remove(most_fails)
                count_speed_violations[index] -= 1.0

        count_speed_violations[most_fails] = 0
        count += 1

    df["iquam_track"] = iquam_track

    return df
