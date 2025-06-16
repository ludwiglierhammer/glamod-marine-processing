"""Module containing main QC functions which could be applied on a DataBundle."""

from __future__ import annotations

import math
from datetime import datetime

from .astronomical_geometry import sunangle
from .auxiliary import convert_units, failed, isvalid, passed, untestable
from .external_clim import Climatology, inspect_climatology
from .time_control import dayinyear, get_month_lengths, split_date


def value_check(inval: float | None) -> int:
    """Check if a value is equal to None

    Parameters
    ----------
    inval : float or None
        The input value to be tested

    Returns
    -------
    int
        Returns 1 if the input value is numerically invalid or None, 0 otherwise
    """
    if isvalid(inval):
        return passed
    return failed


@convert_units(latitude="degrees", longitude="degrees")
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
        2 if either latitude or longitude is numerically invalid or None,
        1 if either latitude or longitude is not in valid range,
        0 otherwise
    """
    if not isvalid(latitude):
        return untestable
    if not isvalid(longitude):
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
        2 if either year, month or day is numerically invalid or None,
        1 if the date is not a valid date,
        0 otherwise
    """
    if isinstance(date, datetime):
        date_ = split_date(date)
        year = date_["year"]
        month = date_["month"]
        day = date_["day"]
    if not isvalid(year):
        return untestable
    if not isvalid(month):
        return untestable
    if not isvalid(day):
        return untestable

    if year > 2025 or year < 1850:
        return failed

    if month < 1 or month > 12:
        return failed

    month_lengths = get_month_lengths(year)

    if day < 1 or day > month_lengths[month - 1]:
        return failed

    return passed


def do_time_check(date: datetime | None = None, hour: float | None = None) -> int:
    """
    Check that the time is valid i.e. in the range 0.0 to 23.99999...

    Parameters
    ----------
    date: datetime-like, optional
        Date of report
    hour : float, optional
        hour of the time to be checked

    Returns
    -------
    int
        2 if hour is numerically invalid or None,
        1 if hour is not a valid hour,
        0 otherwise
    """
    if isinstance(date, datetime):
        date_ = split_date(date)
        hour = date_["hour"]
    if not isvalid(hour):
        return untestable

    if hour >= 24 or hour < 0:
        return failed

    return passed


@convert_units(latitude="degrees", longitude="degrees")
def do_day_check(
    date: datetime | None = None,
    year: int | None = None,
    month: int | None = None,
    day: int | None = None,
    hour: float | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    time_since_sun_above_horizon: float | None = None,
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
    latitude : float, optional
        Latitude of report in degrees
    longitude : float, optional
        Longitude of report in degrees
    time_since_sun_above_horizon : float
        Maximum time sun can have been above horizon (or below) to still count as night. Original QC test had this set
        to 1.0 i.e. it was night between one hour after sundown and one hour after sunrise.

    Returns
    -------
    int
        Set to 0 if it is day, 1 otherwise.

    Note
    ----
    In previous versions, ``time_since_sun_above_horizon`` has the default value 1.0 as one hour is used as a
    definition of "day" for marine air temperature QC. Solar heating biases were considered to be negligible mmore
    than one hour after sunset and up to one hour after sunrise.
    """
    if isinstance(date, datetime):
        date_ = split_date(date)
        year = date_["year"]
        month = date_["month"]
        day = date_["day"]
        hour = date_["hour"]

    p_check = do_position_check.__wrapped__(latitude, longitude)
    d_check = do_date_check(year=year, month=month, day=day)
    t_check = do_time_check(hour=hour)

    # Defaults to FAIL if the location, date or time are bad
    if failed in [p_check, d_check, t_check]:
        return failed

    # Defaults to FAIL if the location, date or time are bad
    if untestable in [p_check, d_check, t_check]:
        return untestable

    year2 = year
    day2 = dayinyear(year, month, day)
    hour2 = math.floor(hour)
    minute2 = (hour - math.floor(hour)) * 60.0

    # go back one hour and test if the sun was above the horizon
    if time_since_sun_above_horizon is not None:
        hour2 = hour2 - time_since_sun_above_horizon
    if hour2 < 0:
        hour2 = hour2 + 24.0
        day2 = day2 - 1
        if day2 <= 0:
            year2 = year2 - 1
            day2 = dayinyear(year2, 12, 31)

    lat2 = latitude
    lon2 = longitude
    if latitude == 0:
        lat2 = 0.0001
    if longitude == 0:
        lon2 = 0.0001

    azimuth, elevation, rta, hra, sid, dec = sunangle(
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


def do_missing_value_check(value: float) -> int:
    """
    Check that value is not None or NaN.

    Parameters
    ----------
    value : float
        Value to be checked

    Returns
    -------
    int
        1 if value is missing, 0 otherwise
    """
    return value_check(value)


@inspect_climatology("climatology")
def do_missing_value_clim_check(climatology: float | Climatology, **kwargs) -> int:
    """
    Check that climatological value is present

    Parameters
    ----------
    climatology : float or Climatology
        Climatology value
        This could be a float value or Climatology object.

    Returns
    -------
    int
        1 if climatology value is missing, 0 otherwise

    Note
    ----
    If ``climatology`` is a Climatology object, pass ``lon`` and ``lat`` and ``date`` or ``month`` and ``day`` as keyword-arguments!
    """
    return value_check(climatology)


@convert_units(value="unknown", hard_limits="unknown")
def do_hard_limit_check(value: float, hard_limits: tuple[float, float]) -> int:
    """
    Check that value is within hard limits specified by "hard_limits".

    Parameters
    ----------
    value : float
        Value to be checked.
    hard_limits : tuple of float
        A tuple of two floats representing the lower and upper limit.

    Returns
    -------
    int
        2 if limits[1] is equal or less than limits[0] of if val is numerically invalid or None,
        1 if val is outside the limits,
        0 otherwise
    """
    if hard_limits[1] <= hard_limits[0]:
        return untestable

    if not isvalid(value):
        return untestable

    if hard_limits[0] <= value <= hard_limits[1]:
        return passed

    return failed


@inspect_climatology("climatology", optional="standard_deviation")
@convert_units(value="unknown", climatology="unknown")
def do_climatology_check(
    value: float,
    climatology: float | Climatology,
    maximum_anomaly: float,
    standard_deviation: float | Climatology | None = "default",
    standard_deviation_limits: list | None = None,
    lowbar: float | None = None,
    **kwargs,
) -> int:
    """
    Check that the value is within the prescribed distance from climatology.

    If ``standard_deviation`` is provided, the value is converted into a standardised anomaly. Optionally,
    if ``standard deviation`` is outside the range specified by ``standard_deviation_limits`` then ``standard_deviation``
    is set to whichever of the lower or upper limits is closest.
    If ``lowbar`` is provided, the anomaly must be greater than ``lowbar`` to fail regardless of ``standard_deviation``.


    Parameters
    ----------
    value : float
        Value to be compared to ``climatology``.
    climatology: float or Climatology
        The climatological average to which ``value`` will be compared.
        This could be a float value or Climatology object.
        If it is a Climatology object, pass ``lon`` and ``lat`` and ``date`` or ``month`` and ``day`` as keyword-arguments!
    maximum_anomaly : float
        Largest allowed anomaly.
        If ``standard_deviation`` is provided, this is the largest allowed standardised anomaly.
    standard_deviation : float or Climatology, default: "default"
        The standard deviation which will be used to standardize the anomaly.
        This could be a float value or Climatology object.
        If it is a Climatology object, pass ``lon`` and ``lat`` and ``date`` or ``month`` and ``day`` as keyword-arguments!
        If standard_deviation is "default", set standard_deviation to 1.0.
    standard_deviation_limits : list, optional
        2-element list containing lower and upper limits for ``standard_deviation``.
        If ``standard_deviation`` is outside these limits, ``standard_deviation`` will be set to the nearest limit.
    lowbar: float, optional
        ``maximum_anomaly`` must be greater than ``lowbar`` to fail regardless of ``standard_deviation``.

    Returns
    -------
    int
        2 if either value, climatology, maximum_anomaly or standard_deviation is numerically invalid or None.
        1 if value anomaly is outside allowed bounds
        0 otherwise

    Note
    ----
    If either ``climatology`` or ``standard_deviation`` is a Climatology object,
    pass ``lon`` and ``lat`` and ``date`` or ``month`` and ``day`` as keyword-arguments!
    """
    if (
        not isvalid(value)
        or not isvalid(climatology)
        or not isvalid(maximum_anomaly)
        or not isvalid(standard_deviation)
    ):
        return untestable

    if standard_deviation != "default":
        if not isvalid(standard_deviation):
            return untestable
    else:
        standard_deviation = 1.0

    if maximum_anomaly <= 0:
        return untestable

    if standard_deviation is None:
        standard_deviation = 1.0

    if standard_deviation_limits is not None:
        if standard_deviation_limits[1] <= standard_deviation_limits[0]:
            return untestable

        standard_deviation = max(standard_deviation, standard_deviation_limits[0])
        standard_deviation = min(standard_deviation, standard_deviation_limits[1])

    climate_diff = abs(value - climatology)

    low_check = True
    if lowbar is not None:
        low_check = climate_diff > lowbar

    if climate_diff / standard_deviation > maximum_anomaly and low_check:
        return failed

    return passed


@convert_units(dpt="K", at2="K")
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
        2 if either dpt or at2 is numerically invalid or None,
        1 if supersaturation is detected,
        0 otherwise
    """
    if not isvalid(dpt) or not isvalid(at2):
        return untestable

    if dpt > at2:
        return failed

    return passed


@convert_units(sst="K", freezing_point="K")
def do_sst_freeze_check(
    sst: float,
    freezing_point: float,
    freeze_check_n_sigma: float | None = "default",
    sst_uncertainty: float | None = "default",
) -> int:
    """Compare an input SST to see if it is above freezing.

    This is a simple freezing point check made slightly more complex. We want to check if a
    measurement of SST is above freezing, but there are two problems. First, the freezing point
    can vary from place to place depending on the salinity of the water. Second, there is uncertainty
    in SST measurements. If we place a hard cut-off at -1.8, then we are likely to bias the average
    of many measurements too high when they are near the freezing point - observational error will
    push the measurements randomly higher and lower, and this test will trim out the lower tail, thus
    biasing the result. The inclusion of an SST uncertainty parameter *might* mitigate that and we allow
    that possibility here.

    Parameters
    ----------
    sst : float
        Sea surface temperature to be checked
    freezing_point : float
        Freezing point of seawater to be used in check
    freeze_check_n_sigma : float, optional, default: "default"
        Number of uncertainty standard deviations that sea surface temperature can be
        below the freezing point before the QC check fails.
    sst_uncertainty : float, optional, default: "default"
        the uncertainty in the SST value

    Returns
    -------
    int
        2 if either sst, freezing_point, freeze_check_n_sigma or sst_uncertainty is numerically invalid or None,
        1 if the insst is below freezing point by more than twice the uncertainty,
        0 otherwise

    Note
    ----
    In previous versions, some parameters had default values:

        * ``sst_uncertainty``: 0.0
        * ``freezing_point``: -1.80
        * ``freeze_check_n_sigma``: 2.0
    """
    if not isvalid(sst):
        return untestable
    if not isvalid(sst_uncertainty):
        return untestable
    if not isvalid(freezing_point):
        return untestable
    if not isvalid(freeze_check_n_sigma):
        return untestable

    if freeze_check_n_sigma == "default":
        freeze_check_n_sigma = 0.0

    if sst_uncertainty == "default":
        sst_uncertainty = 0.0

    # fail if SST below the freezing point by more than twice the uncertainty
    if sst < (freezing_point - freeze_check_n_sigma * sst_uncertainty):
        return failed

    return passed


def do_wind_consistency_check(
    wind_speed: float | None,
    wind_direction: int | None,
) -> int:
    """
    Test to compare windspeed to winddirection.

    Parameters
    ----------
    wind_speed : float, optional
        Wind speed
    wind_direction : int, optional
        Wind direction

    Returns
    -------
    int
        2 if either wind_speed or wind_direction is numerically invalid or None,
        1 if windspeed and direction are inconsistent,
        0 otherwise
    """
    if not isvalid(wind_speed) or not isvalid(wind_direction):
        return untestable
    if wind_speed == 0.0 and wind_direction != 0:
        return failed

    if wind_speed != 0.0 and wind_direction == 0:
        return failed

    return passed
