"""Module containing main QC functions which could be applied on a DataBundle."""

from __future__ import annotations

import math
from datetime import datetime

from . import qc
from .qc import failed, passed, untestable


def _split_date(date):
    try:
        year = int(date.year)
        month = int(date.month)
        day = int(date.day)
        hour = date.hour + date.minute / 60.0 + date.second / 3600.0
    except ValueError:
        return None
    return {"year": year, "month": month, "day": day, "hour": hour}


def do_position_check(latitude: float, longitude: float) -> int:
    """
    Perform the positional QC check on the report. Simple check to make sure that the latitude and longitude are
    within the bounds specified by the ICOADS documentation. Latitude is between -90 and 90. Longitude is between
    -180 and 360

    Parameters
    ----------
    latitude : float
        latitude of observation to be checked in degrees
    longitude : float
        longitude of observation to be checked in degree

    Returns
    -------
    int
        1 if either latitude or longitude is invalid, 0 otherwise
    """
    if qc.isvalid(latitude):
        return untestable
    if qc.isvalid(longitude):
        return untestable

    if latitude < -90 or latitude > 90:
        return failed
    if longitude < -180 or longitude > 360:
        return failed

    return passed


def do_date_check(
    date: datetime | None = None,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
) -> int:
    """
    Perform the date QC check on the report. Check that the date is valid.

    Parameters
    ----------
    date: datetime-like, optional
        Date of observation to be checked
    year : int, optional
        Year of observation to be checked
    month : int, optional
        Month of observation (1-12) to be checked
    day : int, optional
        Day of observation to be checked

    Returns
    -------
    int
        1 if the date is invalid, 0 otherwise
    """
    # Do we need this function?
    # I think this function should return a boolean value, isn't it?
    # maybe return qc.date_check(latitude, longitude)
    # This should already be done while mapping to the CDM.
    if isinstance(date, datetime):
        date_ = _split_date(date)
        if date_ is None:
            return untestable
        year = date_["year"]
        month = date_["month"]
        day = date_["day"]
    if qc.isvalid(year) == failed:
        return untestable
    if qc.isvalid(month) == failed:
        return untestable
    if qc.isvalid(day) == failed:
        return untestable

    if year > 2025 or year < 1850:
        return failed

    if month < 1 or month > 12:
        return failed

    month_lengths = qc.get_month_lengths(year)

    if day < 1 or day > month_lengths[month - 1]:
        return failed

    return passed


def do_time_check(hour: float):
    """
    Check that the time is valid i.e. in the range 0.0 to 23.99999...

    Parameters
    ----------
    hour : float
        hour of the time to be checked

    Returns
    -------
    int
        Return 1 if hour is invalid, 0 otherwise
    """
    if qc.isvalid(hour) == failed:
        return failed

    if hour >= 24 or hour < 0:
        return failed

    return passed


def do_day_check(
    date: datetime | None = None,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    hour: float | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    time_since_sun_above_horizon: float = 1.0,
) -> int:
    """Given year month day hour lat and long calculate if the sun was above the horizon an hour ago.

    This is the "day" test used to decide whether a Marine Air Temperature (MAT) measurement is
    a Night MAT (NMAT) or a Day (MAT). This is important because solar heating of the ship biases
    the MAT measurements. It uses the function sunangle to calculate the elevation of the sun.

    Parameters
    ----------
    date: datetime-like, optional
        Date of report
    year : int, optional
        Year of report
    month : int, optional
        Month of report
    day : int, optional
        Day of report
    hour : float, optional
        Hour of report with minutes as decimal part of hour
    latitude : float
        Latitude of report in degrees
    longitude : float
        Longitude of report in degrees
    time_since_sun_above_horizon : float
        Maximum time sun can have been above horizon (or below) to still count as night. Original QC test had this set
        to 1.0 i.e. it was night between one hour after sundown and one hour after sunrise.

    Returns
    -------
    int
        Set to 0 if it is day, 1 otherwise.
    """
    if isinstance(date, datetime):
        date_ = _split_date(date)
        if date_ is None:
            return failed
        year = date_["year"]
        month = date_["month"]
        day = date_["day"]
        hour = date_["hour"]

    # Defaults to FAIL if the location, date or time are bad
    if (
        do_position_check(latitude, longitude) == 1
        or do_date_check(year=year, month=month, day=day) == 1
        or do_time_check(hour) == 1
    ):
        return failed

    # I don't think these tests will ever be reached because we already do three checks beforehand
    # that rule them out.
    # if not (1 <= month <= 12):
    #     raise ValueError("Month not in range 1-12")
    # if not (1 <= day <= 31):
    #     raise ValueError("Day not in range 1-31")
    # if not (0 <= hour <= 24):
    #     raise ValueError("Hour not in range 0-24")
    # if not (90 >= latitude >= -90):
    #     raise ValueError("Latitude not in range -90 to 90")
    #
    # if year is None or month is None or day is None or hour is None:
    #     return 0

    year2 = year
    day2 = qc.dayinyear(year, month, day)
    hour2 = math.floor(hour)
    minute2 = (hour - math.floor(hour)) * 60.0

    # go back one hour and test if the sun was above the horizon
    hour2 = hour2 - time_since_sun_above_horizon
    if hour2 < 0:
        hour2 = hour2 + 24.0
        day2 = day2 - 1
        if day2 <= 0:
            year2 = year2 - 1
            day2 = qc.dayinyear(year2, 12, 31)

    lat2 = latitude
    lon2 = longitude
    if latitude == 0:
        lat2 = 0.0001
    if longitude == 0:
        lon2 = 0.0001

    azimuth, elevation, rta, hra, sid, dec = qc.sunangle(
        year2, day2, hour2, minute2, 0, 0, 0, lat2, lon2
    )
    del azimuth
    del rta
    del hra
    del sid
    del dec

    if elevation > 0:
        return passed

    return failed


def do_air_temperature_missing_value_check(at: float) -> int:
    """
    Check that air temperature value exists

    Parameters
    ----------
    at : float
        Air temperature

    Returns
    -------
    int
        1 if value is missing, 0 otherwise
    """
    return qc.isvalid(at)


def do_air_temperature_anomaly_check(
    at: float, at_climatology: float, maximum_anomaly: float
) -> int:
    """
    Check that the air temperature is within the prescribed distance from climatology/

    Parameters
    ----------
    at : float
        Air temperature
    at_climatology: float
        Climatological air temperature value
    maximum_anomaly : float
        Maximum_anomaly allowed anomaly

    Returns
    -------
    int
        1 if air temperature anomaly is outside allowed bounds, 0 otherwise
    """
    return qc.climatology_check(at, at_climatology, maximum_anomaly)


def do_air_temperature_no_normal_check(at_climatology: float | None) -> int:
    """
    Check that climatological value is present

    Parameters
    ----------
    at_climatology : float or None
        Air temperature climatology value

    Returns
    -------
    int
        1 if climatology value is missing, 0 otherwise
    """
    return qc.isvalid(at_climatology)


def do_air_temperature_hard_limit_check(at: float, hard_limits: list) -> int:
    """
    Check that air temperature is within hard limits specified by "hard_limits".

    Parameters
    ----------
    at : float
        Air temperature to be checked.
    hard_limits : list
        2-element list containing lower and upper hard limits for the QC check.

    Returns
    -------
    int
        1 if air temperature is outside hard limits, 0 otherwise
    """
    return qc.hard_limit(at, hard_limits)


def do_air_temperature_climatology_plus_stdev_check(
    at: float,
    at_climatology: float,
    at_stdev: float,
    minmax_standard_deviation: list,
    maximum_standardised_anomaly: float,
) -> int:
    """Check that standardised air temperature anomaly is within specified range.

    Temperature is converted into a standardised anomaly by subtracting the climatological normal and dividing by
    the climatological standard deviation. If the climatological standard deviation is outside the range specified by
    "minmax_standard_deviation" then the standard deviation is set to whichever of the lower or upper limits is
    closest. The test fails if the standardised anomaly is larger than the "maximum_standardised_anomaly".

    Parameters
    ----------
    at : float
        Air temperature.
    at_climatology : float
        Climatological normal of air temperatures.
    at_stdev : float
        Climatological standard deviation of air temperatures.
    minmax_standard_deviation : list
        2-element list containing lower and upper limits for standard deviation. If the at_stdev is outside these
        limits, at_stdev will be set to the nearest limit.
    maximum_standardised_anomaly : float
        Largest allowed standardised anomaly

    Returns
    -------
    int
        Returns 1 if standardised temperature anomaly is outside specified range, 0 otherwise.
    """
    return qc.climatology_plus_stdev_check(
        at,
        at_climatology,
        at_stdev,
        minmax_standard_deviation,
        maximum_standardised_anomaly,
    )


"""
Replaced the do_base_mat_qc by four separate functions see above
"""


def do_dpt_climatology_plus_stdev_check(
    dpt: float,
    dpt_climatology: float,
    dpt_stdev: float,
    minmax_standard_deviation: float,
    maximum_standardised_anomaly: float,
) -> int:
    """Check that standardised dewpoint temperature anomaly is within specified range.

    Temperature is converted into a standardised anomaly by subtracting the climatological normal and dividing by
    the climatological standard deviation. If the climatological standard deviation is outside the range specified in
    "minmax_standard_deviation" then the standard deviation is set to whichever of the lower or upper limits is
    closest. The test fails if the standardised anomaly is larger than the "maximum_standardised_anomaly".

    Parameters
    ----------
    dpt : float
        Dewpoint temperature.
    dpt_climatology : float
        Climatological normal of dewpoint temperatures.
    dpt_stdev : float
        Climatological standard deviation of dewpoint temperatures.
    minmax_standard_deviation : float
        2-element list containing lower and upper limits for standard deviation. If the at_stdev is outside these
        limits, at_stdev will be set to the nearest limit.
    maximum_standardised_anomaly : float
        Largest allowed standardised anomaly

    Returns
    -------
    int
        Returns 1 if standardised temperature anomaly is outside specified range, 0 otherwise.
    """
    return qc.climatology_plus_stdev_check(
        dpt,
        dpt_climatology,
        dpt_stdev,
        minmax_standard_deviation,
        maximum_standardised_anomaly,
    )


def do_dpt_missing_value_check(dpt: float) -> int:
    """
    Check that dew point temperature value exists


    Parameters
    ----------
    dpt : float
        Dew point temperature

    Returns
    -------
    int
        1 if value is missing, 0 otherwise
    """
    return qc.isvalid(dpt)


def do_dpt_no_normal_check(dpt_climatology: float) -> int:
    """
    Check that climatological value is present

    Parameters
    ----------
    dpt_climatology : float
        Dew point temperature climatology value

    Returns
    -------
    int
        1 if climatology value is missing, 0 otherwise
    """
    return qc.isvalid(dpt_climatology)


def do_supersaturation_check(dpt: float, at2: float) -> int:
    """
    Perform the super saturation check. Check if a valid dewpoint temperature is greater than a valid air temperature

    Parameters
    ----------
    dpt : float
        Dewpoint temperature
    at2 : float
        Air temperature

    Returns
    -------
    int
        Set to 1 if supersaturation is detected, 0 otherwise
    """
    if qc.isvalid(dpt) == failed or qc.isvalid(at2) == failed:
        return failed
    elif dpt > at2:
        return failed

    return passed


"""
Replaced do_base_dpt_qc with four new functions
"""


def do_sst_missing_value_check(sst):
    """
    Check that sea surface temperature value exists

    Parameters
    ----------
    sst : float
        Sea surface temperature

    Returns
    -------
    int
        1 if value is missing, 0 otherwise
    """
    return qc.isvalid(sst)


def do_sst_freeze_check(
    sst: float, freezing_point: float, freeze_check_n_sigma: float
) -> int:
    """
    Check that sea surface temperature is above freezing

    Parameters
    ----------
    sst : float
        Sea surface temperature
    freezing_point : float
        Freezing point of seawater to be used in check
    freeze_check_n_sigma : float
        Number of uncertainty standard deviations that sea surface temperature can be below the freezing point
        before the QC check fails.

    Returns
    -------
    int
        Return 1 if SST below freezing, 0 otherwise
    """
    return qc.sst_freeze_check(sst, 0.0, freezing_point, freeze_check_n_sigma)


def do_sst_anomaly_check(
    sst: float, sst_climatology: float, maximum_anomaly: float
) -> int:
    """
    Check that the sea surface temperature is within the prescribed distance from climatology/

    Parameters
    ----------
    sst : float
        Sea surface temperature
    sst_climatology: float
        Climatological sea surface temperature value
    maximum_anomaly: float
        Largest allowed anomaly

    Returns
    -------
    int
        1 if sea surface temperature anomaly is outside allowed bounds, 0 otherwise
    """
    return qc.climatology_check(sst, sst_climatology, maximum_anomaly)


def do_sst_no_normal_check(sst_climatology: float) -> int:
    """
    Check that climatological value is present

    Parameters
    ----------
    sst_climatology : float
        Sea surface temperature climatology value

    Returns
    -------
    int
        1 if climatology value is missing, 0 otherwise
    """
    return qc.isvalid(sst_climatology)


def do_wind_speed_missing_value_check(wind_speed: float | None) -> int:
    """Check that wind speed value exists

    Parameters
    ----------
    wind_speed : float or None
        Wind speed

    Returns
    -------
    int
        Returns 1 if wind speed is missing, 0 otherwise.
    """
    return qc.isvalid(wind_speed)


def do_wind_speed_hard_limit_check(
    wind_speed: float | None, hard_limits: list = [0.0, 50.0]
) -> int:
    """Check that wind speed is within hard limits specified by "hard_limits".

    Parameters
    ----------
    wind_speed : float or None
        Wind speed to be checked
    hard_limits : list
        2-element list containing lower and upper limits for QC check

    Returns
    -------
    int
        Returns 1 if wind speed is outside of hard limits, 0 otherwise.
    """
    return qc.hard_limit(wind_speed, hard_limits)


def do_wind_direction_missing_value_check(wind_direction: int | None) -> int:
    """Check that wind direction value exists

    Parameters
    ----------
    wind_direction : int or None
        Wind direction

    Returns
    -------
    int
        Returns 1 if wind speed is missing, 0 otherwise.
    """
    return qc.isvalid(wind_direction)


def do_wind_direction_hard_limit_check(
    wind_direction: int | None, hard_limits: list = [0, 360]
) -> int:
    """Check that wind direction is within hard limits specified by "hard_limits".

    Parameters
    ----------
    wind_direction : int or None
        Wind direction to be checked
    hard_limits : list
        2-element list containing lower and upper limits for QC check

    Returns
    -------
    int
        Returns 1 if wind speed is outside of hard limits, 0 otherwise.
    """
    return qc.hard_limit(wind_direction, hard_limits)


def do_wind_consistency_check(
    wind_speed: float | None,
    wind_direction: int | None,
) -> int:
    """
    Test to compare windspeed to winddirection.

    Parameters
    ----------
    wind_speed : float
        Wind speed
    wind_direction : int
        Wind direction

    Returns
    -------
    int
        1 if windspeed and direction are inconsistent, 0 otherwise
    """
    if qc.isvalid(wind_speed) == failed or qc.isvalid(wind_direction) == failed:
        return failed
    if wind_speed == 0.0 and wind_direction != 0:
        return failed

    if wind_speed != 0.0 and wind_direction == 0:
        return failed

    return passed
