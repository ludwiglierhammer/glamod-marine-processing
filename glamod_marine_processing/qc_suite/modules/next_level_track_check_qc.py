from __future__ import annotations

import numpy as np
import pandas as pd

import glamod_marine_processing.qc_suite.modules.qc as qc
import glamod_marine_processing.qc_suite.modules.spherical_geometry as sg
import glamod_marine_processing.qc_suite.modules.track_check as tc

km_to_nm = 0.539957


def spike_check(df: pd.DataFrame) -> pd.DataFrame:
    """Perform IQUAM like spike check.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data, must have columns 'sst', 'lat', 'lon', 'pt', 'date'

    Returns
    -------
    pd.DataFrame
        DataFrame as original but with 'spike' column added containing the spike check flags

    Raises
    ------
    KeyError
        Raised when one of the required columns is missing from the DataFrame
    """
    for key in ["sst", "lat", "lon", "pt", "date"]:
        if key not in df:
            raise KeyError(f"{key} not in dataframe")

    max_gradient_space = 0.5  # K/km
    max_gradient_time = 1.0  # K/hr

    ship_delta_t = 2.0  # K
    buoy_delta_t = 1.0  # K

    n_neighbours = 5

    numobs = len(df)

    if df.iloc[0].pt in [6, 7]:
        delta_t = buoy_delta_t
    else:
        delta_t = ship_delta_t

    gradient_violations = []
    count_gradient_violations = []

    spike_qc = np.zeros(numobs)

    for t1 in range(numobs):

        violations_for_this_report = []
        count_violations_this_report = 0.0

        lo = max(0, t1 - n_neighbours)
        hi = min(numobs, t1 + n_neighbours + 1)

        for t2 in range(lo, hi):

            row1 = df.iloc[t1]
            row2 = df.iloc[t2]

            if row1.sst is not None and row2.sst is not None:

                distance = sg.sphere_distance(row1.lat, row1.lon, row2.lat, row2.lon)
                time_diff = abs(
                    (row2.date - row1.date).days * 24
                    + (row2.date - row1.date).seconds / 3600.0
                )
                val_change = abs(row2.sst - row1.sst)

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

    count = 0
    while np.sum(count_gradient_violations) > 0.0:
        most_fails = np.argmax(count_gradient_violations)
        spike_qc[most_fails] = 1

        for index in gradient_violations[most_fails]:
            if most_fails in gradient_violations[index]:
                gradient_violations[index].remove(most_fails)
                count_gradient_violations[index] -= 1.0

        count_gradient_violations[most_fails] = 0
        count += 1

    df["spike"] = spike_qc

    return df


def row_difference(
    later_row: pd.DataFrame, earlier_row: pd.DataFrame
) -> (float, float, float, float):
    """Subtracting one row from another to return the speed, distance, course and the time difference between the
    two rows. Originally this was coded as a subtraction: later_row minus earlier_row.

    Parameters
    ----------
    later_row : pd.DataFrame
        The later of the two rows from a DataFrame
    earlier_row : pd.DataFrame
        The earlier of the two rows from a DataFrame

    Returns
    -------
    (float, float, float, float)
        Returns the speed, distance, course and time difference between the two rows
    """
    distance = sg.sphere_distance(
        later_row.lat, later_row.lon, earlier_row.lat, earlier_row.lon
    )

    timediff = qc.time_difference(
        earlier_row.date.year,
        earlier_row.date.month,
        earlier_row.date.day,
        earlier_row.date.hour,
        later_row.date.year,
        later_row.date.month,
        later_row.date.day,
        later_row.date.hour,
    )
    if timediff != 0 and timediff is not None:
        speed = distance / abs(timediff)
    else:
        timediff = 0.0
        speed = distance

    course = sg.course_between_points(
        earlier_row.lat, earlier_row.lon, later_row.lat, later_row.lon
    )

    return speed, distance, course, timediff


def calculate_speed_course_distance_time_difference(df):
    """The speeds and courses calculated using consecutive reports."""
    numobs = len(df)

    speed = np.empty(numobs)
    course = np.empty(numobs)
    distance = np.empty(numobs)
    time_diff = np.empty(numobs)

    speed.fill(np.nan)
    course.fill(np.nan)
    distance.fill(np.nan)
    time_diff.fill(np.nan)

    if numobs > 1:
        for i in range(1, numobs):
            row2 = df.iloc[i]
            row1 = df.iloc[i - 1]
            shpspd, shpdis, shpdir, tdiff = row_difference(row2, row1)

            speed[i] = shpspd
            course[i] = shpdir
            distance[i] = shpdis
            time_diff[i] = tdiff

    df["speed"] = speed
    df["course"] = course
    df["distance"] = distance
    df["time_diff"] = time_diff

    return df


def calc_alternate_speeds(df):
    """The speeds and courses can also be calculated using alternating reports."""
    numobs = len(df)

    alt_speed = np.empty(numobs)
    alt_course = np.empty(numobs)
    alt_distance = np.empty(numobs)
    alt_time_diff = np.empty(numobs)

    alt_speed.fill(np.nan)
    alt_course.fill(np.nan)
    alt_distance.fill(np.nan)
    alt_time_diff.fill(np.nan)

    if numobs > 2:
        for i in range(1, numobs - 1):
            row2 = df.iloc[i + 1]
            row1 = df.iloc[i - 1]
            shpspd, shpdis, shpdir, tdiff = row_difference(row1, row2)

            alt_speed[i] = shpspd
            alt_course[i] = shpdir
            alt_distance[i] = shpdis
            alt_time_diff[i] = tdiff

    df["alt_speed"] = alt_speed
    df["alt_course"] = alt_course
    df["alt_distance"] = alt_distance
    df["alt_time_diff"] = alt_time_diff

    return df


def distr1(df):
    """
    calculate what the distance is between the projected position (based on the reported
    speed and heading at the current and previous time steps) and the actual position. The
    observations are taken in time order.

    :return: list of distances from estimated positions
    :rtype: list of floats

    This takes the speed and direction reported by the ship and projects it forwards half a
    time step, it then projects it forwards another half time step using the speed and
    direction for the next report, to which the projected location
    is then compared. The distances between the projected and actual locations is returned
    """
    nobs = len(df)

    distance_from_est_location = [None]

    for i in range(1, nobs):

        vsi = df.iloc[i].vsi
        vsi_minus_one = df.iloc[i - 1].vsi
        dsi = df.iloc[i].dsi
        dsi_minus_one = df.iloc[i - 1].dsi
        time_diff = df.iloc[i].time_diff

        if (
            vsi is not None
            and vsi_minus_one is not None
            and dsi is not None
            and dsi_minus_one is not None
            and time_diff is not None
        ):
            # get increment from initial position
            lat1, lon1 = tc.increment_position(
                df.iloc[i - 1].lat,
                df.iloc[i - 1].lon,
                df.iloc[i - 1].vsi / km_to_nm,
                df.iloc[i - 1].dsi,
                df.iloc[i].time_diff,
            )

            lat2, lon2 = tc.increment_position(
                df.iloc[i].lat,
                df.iloc[i].lon,
                df.iloc[i].vsi / km_to_nm,
                df.iloc[i].dsi,
                df.iloc[i].time_diff,
            )
            # apply increments to the lat and lon at i-1
            alatx = df.iloc[i - 1].lat + lat1 + lat2
            alonx = df.iloc[i - 1].lon + lon1 + lon2

            # calculate distance between calculated position and the second reported position
            discrepancy = sg.sphere_distance(
                df.iloc[i].lat, df.iloc[i].lon, alatx, alonx
            )

            distance_from_est_location.append(discrepancy)

        else:
            # in the absence of reported speed and direction set to None
            distance_from_est_location.append(None)

    return distance_from_est_location


def distr2(df):
    """Calculate what the distance is between the projected position (based on the reported speed and
    heading at the current and previous time steps) and the actual position. The calculation proceeds from the
    final, later observation to the first (in contrast to distr1 which runs in time order)

    This takes the speed and direction reported by the ship and projects it forwards half a time step, it then
    projects it forwards another half time step using the speed and direction for the next report, to which the
    projected location is then compared. The distances between the projected and actual locations is returned

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    list
        Returns list of distances from estimated positions
    """
    nobs = len(df)

    distance_from_est_location = [None]

    for i in range(nobs - 1, 0, -1):

        vsi = df.iloc[i].vsi
        vsi_minus_one = df.iloc[i - 1].vsi
        dsi = df.iloc[i].dsi
        dsi_minus_one = df.iloc[i - 1].dsi
        time_diff = df.iloc[i].time_diff

        if (
            vsi is not None
            and vsi_minus_one is not None
            and dsi is not None
            and dsi_minus_one is not None
            and time_diff is not None
        ):
            # get increment from initial position - backwards in time
            # means reversing the direction by 180 degrees
            lat1, lon1 = tc.increment_position(
                df.iloc[i].lat,
                df.iloc[i].lon,
                df.iloc[i].vsi / km_to_nm,
                df.iloc[i].dsi - 180.0,
                df.iloc[i].time_diff,
            )

            lat2, lon2 = tc.increment_position(
                df.iloc[i - 1].lat,
                df.iloc[i - 1].lon,
                df.iloc[i - 1].vsi / km_to_nm,
                df.iloc[i - 1].dsi - 180.0,
                df.iloc[i].time_diff,
            )

            # apply increments to the lat and lon at i-1
            alatx = df.iloc[i].lat + lat1 + lat2
            alonx = df.iloc[i].lon + lon1 + lon2

            # calculate distance between calculated position and the second reported position
            discrepancy = sg.sphere_distance(
                df.iloc[i - 1].lat, df.iloc[i - 1].lon, alatx, alonx
            )
            distance_from_est_location.append(discrepancy)

        else:
            # in the absence of reported speed and direction set to None
            distance_from_est_location.append(None)

    # that fancy bit at the end reverses the array
    return distance_from_est_location[::-1]


def midpt(df: pd.DataFrame) -> list:
    """Interpolate between alternate reports and compare the interpolated location to the actual location. e.g.
    take difference between reports 2 and 4 and interpolate to get an estimate for the position at the time
    of report 3. Then compare the estimated and actual positions at the time of report 3.

    The calculation linearly interpolates the latitudes and longitudes (allowing for wrapping around the
    dateline and so on).

    Parameters
    ----------
    df : pd.DataFrame
        Input data

    Returns
    -------
    list
        Returns list of distances from estimated positions in km
    """
    nobs = len(df)

    midpoint_discrepancies = [None]

    for i in range(1, nobs - 1):
        t0 = df.iloc[i].time_diff  # self.getvar(i, "time_diff")
        t1 = df.iloc[i + 1].time_diff  # self.getvar(i + 1, "time_diff")

        if t0 is not None and t1 is not None:
            if t0 + t1 != 0:
                fraction_of_time_diff = t0 / (t0 + t1)
            else:
                fraction_of_time_diff = 0.0
        else:
            fraction_of_time_diff = 0.0

        if fraction_of_time_diff > 1.0:
            print(fraction_of_time_diff, t0, t1)

        estimated_lat_at_midpt, estimated_lon_at_midpt = sg.intermediate_point(
            df.iloc[i - 1].lat,
            df.iloc[i - 1].lon,
            df.iloc[i + 1].lat,
            df.iloc[i + 1].lon,
            fraction_of_time_diff,
        )

        discrepancy = sg.sphere_distance(
            df.iloc[i].lat,
            df.iloc[i].lon,
            estimated_lat_at_midpt,
            estimated_lon_at_midpt,
        )

        midpoint_discrepancies.append(discrepancy)

    midpoint_discrepancies.append(None)

    return midpoint_discrepancies


def track_check(df: pd.DataFrame):
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
        return

    # Generic ids and buoys get a free pass on the track check
    if qc.id_is_generic(df.iloc[0].id, df.iloc[0].date.year) or df.iloc[0].pt in [6, 7]:
        for i in range(0, nobs):
            df["trk"] = np.zeros(nobs)
            df["few"] = np.zeros(nobs)
        return

    # fewer than three obs - set the fewsome flag
    # deck 720 gets a pass prior to 1891 see
    # Carella, Kent, Berry 2015 Appendix A3
    if nobs < 3:
        if df.iloc[0].dck == 720 and df.iloc[0].date.year < 1891:
            df["trk"] = np.zeros(nobs)
            df["few"] = np.zeros(nobs)
            return
        else:
            df["trk"] = np.zeros(nobs)
            df["few"] = np.zeros(nobs) + 1
            return

    trk = np.zeros(nobs)
    few = np.zeros(nobs)

    # work out speeds and distances between alternating points
    df = calc_alternate_speeds(df)
    df = calculate_speed_course_distance_time_difference(df)

    # what are the mean and mode speeds?
    modal_speed = tc.modesp(df.speed)

    # set speed limits based on modal speed
    amax, amaxx, amin = tc.set_speed_limits(modal_speed)
    del amaxx
    del amin
    # compare reported speeds and positions if we have them
    forward_diff_from_estimated = distr1(df)
    reverse_diff_from_estimated = distr2(df)

    df["fwd_diff"] = forward_diff_from_estimated
    df["bwd_diff"] = reverse_diff_from_estimated

    try:
        midpoint_diff_from_estimated = midpt(df)
    except Exception:
        print(df.iloc[0].id)
        assert False

    df["midpt"] = midpoint_diff_from_estimated

    # do QC
    trk = np.zeros(nobs)
    few = np.zeros(nobs)

    for i in range(1, nobs - 1):
        thisqc_a = 0
        thisqc_b = 0

        # together these cover the speeds calculate from point i
        if (
            df.iloc[i].speed is not None
            and df.iloc[i].speed > amax
            and df.iloc[i - 1].alt_speed is not None
            and df.iloc[i - 1].alt_speed > amax
        ):
            thisqc_a += 1.00
        elif (
            df.iloc[i + 1].speed is not None
            and df.iloc[i + 1].speed > amax
            and df.iloc[i + 1].alt_speed is not None
            and df.iloc[i + 1].alt_speed > amax
        ):
            thisqc_a += 2.00
        elif (
            df.iloc[i].speed is not None
            and df.iloc[i].speed > amax
            and df.iloc[i + 1].speed is not None
            and df.iloc[i + 1].speed > amax
        ):
            thisqc_a += 3.00

        # Quality-control by examining the distance
        # between the calculated and reported second position.
        thisqc_b += tc.check_distance_from_estimate(
            df.iloc[i].vsi,
            df.iloc[i - 1].vsi,
            df.iloc[i].time_diff,
            forward_diff_from_estimated[i],
            reverse_diff_from_estimated[i],
        )
        # Check for continuity of direction
        thisqc_b += tc.direction_continuity(
            df.iloc[i].dsi,
            df.iloc[i - 1].dsi,
            df.iloc[i].course,
            max_direction_change,
        )
        # Check for continuity of speed.
        thisqc_b += tc.speed_continuity(
            df.iloc[i].vsi,
            df.iloc[i - 1].vsi,
            df.iloc[i].speed,
            max_speed_change,
        )

        # check for speeds in excess of 40.00 knots
        if df.iloc[i].speed > max_absolute_speed / km_to_nm:
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

    df["trk"] = trk
    df["few"] = few

    return df
