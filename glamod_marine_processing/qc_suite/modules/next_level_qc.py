"""Module containing main QC functions which could be applied on a DataBundle."""

from __future__ import annotations

import math

from . import qc

# This should be the raw structure.
# In general, I think, we do not need to set qc flags, we just return them (no self.set_qc)
# I hop I did not forget anything.


def is_buoy(platform_type: int) -> int:
    """
    Identify whether report is from a moored or drifting buoy based on ICOADS platform type PT.

    Parameters
    ----------
    platform_type : int
        Platform type

    Returns
    -------
    int
        Return 1 if observation is from a drifting or moored buoy and 0 otherwise
    """
    # Do we need this function?
    # Where/Why do we need "isbuoy" and "isdrifter"?
    # I think this function should return a boolean value, isn't it?
    # I think we should use the CDM platform table?
    # https://glamod.github.io/cdm-obs-documentation/tables/code_tables/platform_type/platform_type.html
    if platform_type in [6, 7]:
        return 1
    else:
        return 0


def is_drifter(platform_type: int) -> int:
    """
    Identify whether report is from a drifting buoy based on ICOADS platform type PT.
    trackqc is only applied to drifting buoys. Used to filter drifting buoys.

    Parameters
    ----------
    platform_type : int
        Platform type

    Returns
    -------
    int
        Return 1 if observation is from a drifting buoy and 0 otherwise
    """
    if platform_type == 7:
        return 1
    else:
        return 0


def is_ship(platform_type: int) -> int:
    """
    Identify whether report is from a ship based on ICOADS platform type PT.
    Marien Air Temperature QC only performed on reports from ships. Used to filter ships.

    Parameters
    ----------
    platform_type : int
        Platform type

    Returns
    -------
    int
        Return 1 if observation is from a ship and 0 otherwise
    """
    # Do we need this function?
    # I think this function should return a boolean value, isn't it?
    # I think we should use the CDM platform table?
    # https://glamod.github.io/cdm-obs-documentation/tables/code_tables/platform_type/platform_type.html
    if platform_type in [0, 1, 2, 3, 4, 5, 10, 11, 12, 17]:
        return 1
    else:
        return 0


def is_deck_780(dck: int) -> int:
    """
    Identify obs that are from ICOADS Deck 780 which consists of obs from WOD.
    Observations from deck 780 are not used so they are not included in QC.

    Parameters
    ----------
    dck : int
        Deck of observation

    Returns
    -------
    int
        return 1 if observation is in deck 780 and 0 otherwise
    """
    # Do we need this function?
    # Where/Why do we need "is780"?
    # I think this function should return a boolean value, isn't it?
    # We do not have this information explicitly in the CDM.
    if dck == 780:
        return 1
    else:
        return 0


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

    Raises
    ------
    ValueError
        When latitude or longitude is None or non-finite
    """
    if latitude is None or math.isnan(latitude):
        raise ValueError("Latitude is None or non-finite")
    if longitude is None or math.isnan(longitude):
        raise ValueError("Longitude is None or non-finite")

    result = 0
    if latitude < -90 or latitude > 90:
        result = 1
    if longitude < -180 or longitude > 360:
        result = 1

    return result


def do_date_check(year: int, month: int, day: int) -> int:
    """
    Perform the date QC check on the report. Check that the date is valid.

    Parameters
    ----------
    year : int
        Year of observation to be checked
    month : int
        Month of observation (1-12) to be checked
    day : int
        Day of observation to be checked

    Returns
    -------
    int
        1 if the date is invalid, 0 otherwise

    Raises
    ------
    ValueError
        when Year or Month is set to None
    """
    # Do we need this function?
    # I think this function should return a boolean value, isn't it?
    # maybe return qc.date_check(latitude, longitude)
    # This should already be done while mapping to the CDM.
    if year is None:
        raise ValueError("Year is set to None")
    if month is None:
        raise ValueError("Month is set to None")

    result = 0

    if year > 2024 or year < 1850:
        result = 1

    if month < 1 or month > 12:
        result = 1

    month_lengths = qc.get_month_lengths(year)

    if day is None:
        result = 1
    else:
        if day < 1 or day > month_lengths[month - 1]:
            result = 1

    return result


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
    result = 0

    if hour is not None and (hour >= 24 or hour < 0):
        result = 1

    if hour is None:
        result = 1

    return result


def do_blacklist(
    id: str,
    deck: int,
    year: int,
    month: int,
    latitude: float,
    longitude: float,
    platform_type: int,
) -> int:
    """
    Do basic blacklisting on the report. The blacklist is used to remove data that are known to be bad
    and shouldn't be passed to the QC.

    If the report is from Deck 732, compares the observations year and location to a table of pre-identified
    regions in which Deck 732 observations are known to be dubious - see Rayner et al. 2006 and Kennedy et al.
    2011b. Observations at 0 degrees latitude 0 degrees longitude are blacklisted as this is a common error.
    C-MAN stations with platform type 13 are blacklisted. SEAS data from deck 874 are unreliable (SSTs were
    often in excess of 50degC) and so the whole deck was removed from processing.

    Parameters
    ----------
    id : str
        ID of the report
    deck : int
        Deck of the report
    year : int
        Year of the report
    month : int
        Month of the report (1-12)
    latitude: float
        Latitude of the report
    longitude : float
        Longitude of the report
    platform_type : int
        Platform type of report

    Returns
    -------
    int
        1 if the report is blacklisted, 0 otherwise
    """
    # Fold longitudes into ICOADS range
    if longitude > 180.0:
        longitude -= 360

    result = 0

    if latitude == 0.0 and longitude == 0.0:
        result = 1  # blacklist all obs at 0,0 as this is a common error.

    if platform_type is not None and platform_type == 13:
        result = 1  # C-MAN data - we do not want coastal stations

    if id == "SUPERIGORINA":
        result = 1

    # these are the definitions of the regions which are blacklisted for Deck 732
    region = {
        1: [-175, 40, -170, 55],
        2: [-165, 40, -160, 60],
        3: [-145, 40, -140, 50],
        4: [-140, 30, -135, 40],
        5: [-140, 50, -130, 55],
        6: [-70, 35, -60, 40],
        7: [-50, 45, -40, 50],
        8: [5, 70, 10, 80],
        9: [0, -10, 10, 0],
        10: [-30, -25, -25, -20],
        11: [-60, -50, -55, -45],
        12: [75, -20, 80, -15],
        13: [50, -30, 60, -20],
        14: [30, -40, 40, -30],
        15: [20, 60, 25, 65],
        16: [0, -40, 10, -30],
        17: [-135, 30, -130, 40],
    }

    # this dictionary contains the regions that are to be excluded for this year
    year_to_regions = {
        1958: [1, 2, 3, 4, 5, 6, 14, 15],
        1959: [1, 2, 3, 4, 5, 6, 14, 15],
        1960: [1, 2, 3, 5, 6, 9, 14, 15],
        1961: [1, 2, 3, 5, 6, 14, 15, 16],
        1962: [1, 2, 3, 5, 12, 13, 14, 15, 16],
        1963: [1, 2, 3, 5, 6, 12, 13, 14, 15, 16],
        1964: [1, 2, 3, 5, 6, 12, 13, 14, 16],
        1965: [1, 2, 6, 10, 12, 13, 14, 15, 16],
        1966: [1, 2, 6, 9, 14, 15, 16],
        1967: [1, 2, 5, 6, 9, 14, 15],
        1968: [1, 2, 3, 5, 6, 9, 14, 15],
        1969: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16],
        1970: [1, 2, 3, 4, 5, 6, 8, 9, 14, 15],
        1971: [1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 16],
        1972: [4, 7, 8, 9, 10, 11, 13, 16, 17],
        1973: [4, 7, 8, 10, 11, 13, 16, 17],
        1974: [4, 7, 8, 10, 11, 16, 17],
    }

    if deck == 732:
        if year in year_to_regions:
            regions_to_check = year_to_regions[year]
            for regid in regions_to_check:
                thisreg = region[regid]
                if (
                    thisreg[0] <= longitude <= thisreg[2]
                    and thisreg[1] <= latitude <= thisreg[3]
                ):
                    result = 1

    if deck == 874:
        result = 1  # SEAS data gets blacklisted

    # For a short period, observations from drifting buoys with these IDs had very erroneous values in the
    # Tropical Pacific. These were identified offline and added to the blacklist
    if (
        (year == 2005 and month == 11)
        or (year == 2005 and month == 12)
        or (year == 2006 and month == 1)
    ):
        if id in [
            "53521    ",
            "53522    ",
            "53566    ",
            "53567    ",
            "53568    ",
            "53571    ",
            "53578    ",
            "53580    ",
            "53582    ",
            "53591    ",
            "53592    ",
            "53593    ",
            "53594    ",
            "53595    ",
            "53596    ",
            "53599    ",
            "53600    ",
            "53601    ",
            "53602    ",
            "53603    ",
            "53604    ",
            "53605    ",
            "53606    ",
            "53607    ",
            "53608    ",
            "53609    ",
            "53901    ",
            "53902    ",
        ]:
            result = 1

    return result


def do_day_check(
    year: int,
    month: int,
    day: int,
    hour: float,
    latitude: float,
    longitude: float,
    time_since_sun_above_horizon: float,
) -> int:
    """Given year month day hour lat and long calculate if the sun was above the horizon an hour ago.

    This is the "day" test used to decide whether a Marine Air Temperature (MAT) measurement is
    a Night MAT (NMAT) or a Day (MAT). This is important because solar heating of the ship biases
    the MAT measurements. It uses the function sunangle to calculate the elevation of the sun.

    Parameters
    ----------
    year : int
        Year of report
    month : int
        Month of report
    day : int
        Day of report
    hour : float
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
        Set to 1 if it is day, 0 otherwise.
    """
    # Defaults to FAIL if the location, date or time are bad
    if (
        do_position_check(latitude, longitude) == 1
        or do_date_check(year, month, day) == 1
        or do_time_check(hour) == 1
    ):
        return 1

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

    result = 0
    if elevation > 0:
        result = 1

    return result


def humidity_blacklist(platform_type: int) -> int:
    """
    Flag certain sources as ineligible for humidity QC.

    Parameters
    ----------
    platform_type : int
        Platform type of report

    Returns
    -------
    int
        Return 1 if report is ineligible for humidity QC, otherwise 0.
    """
    if platform_type in [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 15]:
        return 0
    else:
        return 1


def mat_blacklist(
    platform_type: int,
    deck: int,
    latitude: float,
    longitude: float,
    year: int,
) -> int:
    """
    Flag certain decks, areas and other sources as ineligible for MAT QC.

    These exclusions are based on Kent et al. HadNMAT2 paper and include
    Deck 780 which is oceanographic data and the North Atlantic, Suez,
    Indian Ocean area in the 19th Century.

    Parameters
    -------------
    platform_type: int
        Platform type of report
    deck: int
        Deck number of report
    latitude: float
        Latitude of the report
    longitude: float
         Longitude of the report
    year: int
        Year of the report

    Returns
    ---------
    int
        Returns 1 if report is ineligible for MAT QC, otherwise 0.

    References
    ------------
    https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/jgrd.50152
    """
    result = 0

    # Observations from ICOADS Deck 780 with platform type 5 (originating from
    # the World Ocean Database) [Boyer et al., 2009] were found to be erroneous (Z. Ji and S. Worley, personal
    # communication, 2011) and were excluded from HadNMAT2.
    if platform_type == 5 and deck == 780:
        result = 1

    # North Atlantic, Suez and indian ocean to be excluded from MAT processing
    # See figure 8 from Kent et al.
    if (
        deck == 193
        and 1880 <= year <= 1892
        and (
            (-80.0 <= longitude <= 0.0 and 40.0 <= latitude <= 55.0)
            or (-10.0 <= longitude <= 30.0 and 35.0 <= latitude <= 45.0)
            or (15.0 <= longitude <= 45.0 and -10.0 <= latitude <= 40.0)
            or (15.0 <= longitude <= 95.0 and latitude >= -10.0 and latitude <= 15.0)
            or (95.0 <= longitude <= 105.0 and -10.0 <= latitude <= 5.0)
        )
    ):
        result = 1

    return result


def wind_blacklist(deck):
    """
    Flag certain sources as ineligible for wind QC. Based on Shawn Smith's list.

    Parameters
    ----------
    deck : int
        Deck of report

    Returns
    -------
    int
        Set to 1 if deck is in black list, 0 otherwise
    """
    result = 0
    if deck in [708, 780]:
        result = 1

    return result


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
    return qc.value_check(at)


def do_air_temperature_anomaly_check(
    at: float, at_climatology: float, parameters: dict
) -> int:
    """
    Check that the air temperature is within the prescribed distance from climatology/

    Parameters
    ----------
    at : float
        Air temperature
    at_climatology: float
        Climatological air temperature value
    parameters : dict
        Dictionary containing QC parameters. Must contain key "maximum_anomaly"

    Returns
    -------
    int
        1 if air temperature anomaly is outside allowed bounds, 0 otherwise

    Raises
    ------
    KeyError
        When maximum anomaly is not in parameters dictionary
    """
    if "maximum_anomaly" not in parameters:
        raise KeyError('"maximum anomaly" not in parameters dictionary.')

    return qc.climatology_check(at, at_climatology, parameters["maximum_anomaly"])


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
    return qc.no_normal_check(at_climatology)


def do_air_temperature_hard_limit_check(at: float, parameters: dict) -> int:
    """
    Check that air temperature is within hard limits specified by "hard_limits".

    Parameters
    ----------
    at : float
        Air temperature to be checked.
    parameters : dict
        Dictionary containing QC parameters. Must contain key "hard_limits".

    Returns
    -------
    int
        1 if air temperature is outside hard limits, 0 otherwise

    Raises
    ------
    KeyError
        When "hard_limits" is not in parameters dictionary
    """
    if "hard_limits" not in parameters:
        raise KeyError('"hard_limits" not in parameters dictionary.')
    return qc.hard_limit(at, parameters["hard_limits"])


def do_air_temperature_climatology_plus_stdev_check(
    at: float, at_climatology: float, at_stdev: float, parameters: dict
) -> int:
    """Check that standardised air temperature anomaly is within specified range.

    Temperature is converted into a standardised anomaly by subtracting the climatological normal and dividing by
    the climatological standard deviation. If the climatological standard deviation is outside the range specified in
    the parameters dictionary under "minmax_standard_deviation" then the standard deviation is set to whichever of
    the lower or upper limits is closest. The test fails if the standardised anomaly is larger than the value
    specified in the parameters dictionary under "maximum_standardised_anomaly".

    Parameters
    ----------
    at : float
        Air temperature.
    at_climatology : float
        Climatological normal of air temperatures.
    at_stdev : float
        Climatological standard deviation of air temperatures.
    parameters : dict
        Dictionary containing QC parameters. Must contain keys "minmax_standard_deviation" and
        "maximum_standardised_anomaly"

    Returns
    -------
    int
        Returns 1 if standardised temperature anomaly is outside specified range, 0 otherwise.

    Raises
    ------
    KeyError
        When "minmax_standard_deviation" or "maximum_standardised_anomaly" is not in the dictionary.
    """
    if "minmax_standard_deviation" not in parameters:
        raise KeyError('"minmax_standard_deviation" not in parameters')
    if "maximum_standardised_anomaly" not in parameters:
        raise KeyError('"maximum_standardised_anomaly" not in parameters')
    return qc.climatology_plus_stdev_check(
        at,
        at_climatology,
        at_stdev,
        parameters["minmax_standard_deviation"],
        parameters["maximum_standardised_anomaly"],
    )


"""
Replaced the do_base_mat_qc by four separate functions see above
"""
# def do_base_mat_qc(at, parameters):
#     """Run the base MAT QC checks, non-missing, climatology check and check for normal etc."""
#     # I think this should return a boolean value, isn't it?
#     assert "maximum_anomaly" in parameters
#
#     self.set_qc("AT", "noval", qc.value_check(self.getvar("AT")))
#     self.set_qc(
#         "AT",
#         "clim",
#         qc.climatology_check(
#             self.getvar("AT"), self.getnorm("AT"), parameters["maximum_anomaly"]
#         ),
#     )
#     self.set_qc("AT", "nonorm", qc.no_normal_check(self.getnorm("AT")))
#     self.set_qc(
#         "AT",
#         "hardlimit",
#         qc.hard_limit(self.getvar("AT"), parameters["hard_limits"]),
#     )


def do_dpt_climatology_plus_stdev_check(
    dpt: float, dpt_climatology: float, dpt_stdev: float, parameters: dict
) -> int:
    """Check that standardised dewpoint temperature anomaly is within specified range.

    Temperature is converted into a standardised anomaly by subtracting the climatological normal and dividing by
    the climatological standard deviation. If the climatological standard deviation is outside the range specified in
    the parameters dictionary under "minmax_standard_deviation" then the standard deviation is set to whichever of
    the lower or upper limits is closest. The test fails if the standardised anomaly is larger than the value
    specified in the parameters dictionary under "maximum_standardised_anomaly".

    Parameters
    ----------
    dpt : float
        Dewpoint temperature.
    dpt_climatology : float
        Climatological normal of dewpoint temperatures.
    dpt_stdev : float
        Climatological standard deviation of dewpoint temperatures.
    parameters : dict
        Dictionary containing QC parameters. Must contain keys "minmax_standard_deviation" and
        "maximum_standardised_anomaly"

    Returns
    -------
    int
        Returns 1 if standardised temperature anomaly is outside specified range, 0 otherwise.

    Raises
    ------
    KeyError
        When "minmax_standard_deviation" or "maximum_standardised_anomaly" is not in the dictionary.
    """
    if "minmax_standard_deviation" not in parameters:
        raise KeyError('"minmax_standard_deviation" not in parameters')
    if "maximum_standardised_anomaly" not in parameters:
        raise KeyError('"maximum_standardised_anomaly" not in parameters')
    return qc.climatology_plus_stdev_check(
        dpt,
        dpt_climatology,
        dpt_stdev,
        parameters["minmax_standard_deviation"],
        parameters["maximum_standardised_anomaly"],
    )


def do_dpt_missing_value_check(dpt):
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
    return qc.value_check(dpt)


def do_dpt_no_normal_check(dpt_climatology):
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
    return qc.no_normal_check(dpt_climatology)


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
    result = 0
    if (dpt is None) | (at2 is None):
        result = 1
    elif dpt > at2:
        result = 1

    return result


"""
Replaced do_base_dpt_qc with four new functions
"""
# def do_base_dpt_qc(dpt, parameters):
#     """
#     Run the base DPT checks, non missing, modified climatology check, check for normal,
#     supersaturation etc.
#     """
#     # I think this should return a boolean value, isn't it?
#     self.set_qc(
#         "DPT",
#         "clim",
#         qc.climatology_plus_stdev_check(
#             self.getvar("DPT"),
#             self.getnorm("DPT"),
#             self.getnorm("DPT", "stdev"),
#             parameters["minmax_standard_deviation"],
#             parameters["maximum_standardised_anomaly"],
#         ),
#     )
#
#     self.set_qc("DPT", "noval", qc.value_check(self.getvar("DPT")))
#     self.set_qc("DPT", "nonorm", qc.no_normal_check(self.getnorm("DPT")))
#     self.set_qc(
#         "DPT", "ssat", qc.supersat_check(self.getvar("DPT"), self.getvar("AT2"))
#     )


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
    return qc.value_check(sst)


def do_sst_freeze_check(sst: float, parameters: dict) -> int:
    """
    Check that sea surface temperature is above freezing

    Parameters
    ----------
    sst : float
        Sea surface temperature
    parameters : dict
        Dictionary containing QC parameters. Must contain keys "freezing_point" and "freeze_check_n_sigma"

    Returns
    -------
    int
        Return 1 if SST below freezing, 0 otherwise

    Raises
    ------
    KeyError
        When freezing_point or freeze_check_n_sigma is not in parameters
    """
    if "freezing_point" not in parameters:
        raise KeyError('"freezing_point" not in parameters')
    if "freeze_check_n_sigma" not in parameters:
        raise KeyError('"freeze_check_n_sigma" not in parameters')
    return qc.sst_freeze_check(
        sst, 0.0, parameters["freezing_point"], parameters["freeze_check_n_sigma"]
    )


def do_sst_anomaly_check(sst: float, sst_climatology: float, parameters: dict) -> int:

    """
    Check that the sea surface temperature is within the prescribed distance from climatology/

    Parameters
    ----------
    sst : float
        Sea surface temperature
    sst_climatology: float
        Climatological sea surface temperature value
    parameters : dict
        Dictionary containing QC parameters. Must contain key "maximum_anomaly"

    Returns
    -------
    int
        1 if sea surface temperature anomaly is outside allowed bounds, 0 otherwise

    Raises
    ------
    KeyError
        When maximum anomaly is not in parameters dictionary
    """
    if "maximum_anomaly" not in parameters:
        raise KeyError('"maximum anomaly" not in parameters dictionary.')

    return qc.climatology_check(sst, sst_climatology, parameters["maximum_anomaly"])


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
    return qc.no_normal_check(sst_climatology)


# def do_base_sst_qc(sst, parameters):
#     """
#     Run the base SST QC checks, non-missing, above freezing, climatology check
#     and check for normal
#     """
#     # I think this should return a boolean value, isn't it?
#     assert "freezing_point" in parameters
#     assert "freeze_check_n_sigma" in parameters
#     assert "maximum_anomaly" in parameters
#
#     self.set_qc("SST", "noval", qc.value_check(self.getvar("SST")))
#
#     self.set_qc(
#         "SST",
#         "freez",
#         qc.sst_freeze_check(
#             self.getvar("SST"),
#             0.0,
#             parameters["freezing_point"],
#             parameters["freeze_check_n_sigma"],
#         ),
#     )
#
#     self.set_qc(
#         "SST",
#         "clim",
#         qc.climatology_check(
#             self.getvar("SST"), self.getnorm("SST"), parameters["maximum_anomaly"]
#         ),
#     )
#
#     self.set_qc("SST", "nonorm", qc.no_normal_check(self.getnorm("SST")))
#     self.set_qc(
#         "SST",
#         "hardlimit",
#         qc.hard_limit(self.getvar("SST"), parameters["hard_limits"]),
#     )


def do_wind_missing_value_check(wind_speed: float | None) -> int:
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
    return qc.value_check(wind_speed)


def do_wind_hard_limits_check(wind_speed: float, parameters: dict) -> int:
    """Check that wind speed is within hard limits specified by "hard_limits".

    Parameters
    ----------
    wind_speed : float
        Wind speed to be checked
    parameters : dict
        Dictionary containing QC parameters. Must contain key "hard_limits".

    Returns
    -------
    int
        Returns 1 if wind speed is outside of hard limits, 0 otherwise.
    """
    return qc.hard_limit(wind_speed, parameters["hard_limits"])


def do_wind_consistency_check(wind_speed: float, wind_direction: float, parameters: dict) -> int:

    """
    Test to compare windspeed to winddirection.

    Parameters
    ----------
    wind_speed : float
        Wind speed
    wind_direction : int
        Wind direction in range 1-362 (see ICOADS documentation)
    parameters : dict
        QC with "variable_limit" which is a single value that specifies a maximum wind speed that can correspond to
        variable wind direction.

    Returns
    -------
    int
        1 if windspeed and direction are inconsistent, 0 otherwise
    """
    if "variable_limit" not in parameters:
        raise KeyError('"variable_limit" not in parameters')

    result = 0

    if wind_direction is None or wind_speed is None:
        result = 1
    else:
        # direction 361 is Calm i.e. wind speed should be zero
        if wind_direction == 361 and wind_speed != 0:
            result = 1

        # direction 363 is Variable i.e. low wind speed
        if wind_direction == 362 and wind_speed > parameters["variable_limit"]:
            result = 1

    return result


"""do base wind qc replaced by preceding three functions"""
# def do_base_wind_qc(ws, parameters):
#     """Run the base Wind speed QC checks."""
#     self.set_qc("W", "noval", qc.value_check(self.getvar("W")))
#     self.set_qc(
#         "W", "hardlimit", qc.hard_limit(self.getvar("W"), parameters["hard_limits"])
#     )
#     self.set_qc(
#         "W",
#         "consistency",
#         qc.wind_consistency(
#             self.getvar("W"), self.getvar("D"), parameters["variable_limit"]
#         ),
#     )


"""Only one QC check from do_kate_mat_qc was unique to the function so I added it to air temperature checks above"""
# def do_kate_mat_qc(at, parameters):
#     """
#     Kate's modified MAT checks, non missing, modified climatology check, check for normal etc.
#     Has a mix of AT and AT2 because we want to keep two sets of climatologies and checks for humidity
#     """
#     # I think this should return a boolean value, isn't it?
#     # What is AT and AT2?
#     self.set_qc(
#         "AT2",
#         "clim",
#         qc.climatology_plus_stdev_check(
#             self.getvar("AT2"),
#             self.getnorm("AT2"),
#             self.getnorm("AT2", "stdev"),
#             parameters["minmax_standard_deviation"],
#             parameters["maximum_standardised_anomaly"],
#         ),
#     )
#
#     self.set_qc("AT2", "noval", qc.value_check(self.getvar("AT2")))
#     self.set_qc("AT2", "nonorm", qc.no_normal_check(self.getnorm("AT2")))
#     self.set_qc(
#         "AT2",
#         "hardlimit",
#         qc.hard_limit(self.getvar("AT"), parameters["hard_limits"]),
#     )


# def perform_base_qc(pt, latitude, longitude, timestamp, parameters):
#     """
#     Run all the base QC checks on the header file (CDM).
#     """
#     # If one of those checks is missing we break. Is this reasonable to you?
#
#     # self.do_fix_missing_hour()  # this should already be fixed while mapping to the CDM
#
#     if is_buoy(pt):
#         return "2"  # not checked, since we have no QC for buoys?
#
#     if not is_ship(pt):
#         return "2"  # not checked, since we have a QC for ships only?
#
#     if is_deck_780():
#         return "?"  # I have no idea what do do here
#
#     # Should we filter buoy, ship, deck_780 before this routine?
#     # I think this is too ICOADS-specific, isn't it?
#
#     if not do_position_check(latitude, longitude):
#         return "1"  # failed
#
#     if not do_date_check(year=timestamp.year, month=timestamp.month, day=timestamp.day):
#         return "1"  # failed
#
#     if not do_time_check(timestamp.hour):
#         return "1"  # failed
#
#     do_blacklist()  # I have no idea what do do here
#
#     is_day = do_day_check(
#         parameters["base"]["time_since_sun_above_horizon"]
#     )  # maybe we need this variable afterwards
#
#
# def perform_obs_qc(
#     at=None, dpt=None, slp=None, sst=None, wbt=None, wd=None, ws=None, parameters={}
# ):
#     """Run all the base QC checks on the obsevation files (CDM)."""
#
#     humidity_blacklist()
#     mat_blacklist()
#     wind_blacklist()
#
#     # Should we do those blacklisting before this routine?
#     # Maybe as extra parameters of this function: do_humidity_qc, do_mat_qc, do_wind_qc?
#
#     if at is not None:
#         return do_base_mat_qc(at, parameters)
#         # How should we implement this: self.do_kate_mat_qc(parameters["AT"]) ??
#
#     if dpt is not None:
#         return do_base_dpt_qc(dpt, parameters)
#
#     if slp is not None:
#         return do_base_slp_qc(slp, parameters)
#
#     if sst is not None:
#         return do_base_sst_qc(sst, parameters)
#
#     if ws is not None:  # I think "W" is "WS" in the CDM.
#         return do_base_wind_qc(ws, parameters)
#
#     # special check for silly values in all humidity-related variables
#     # and set DPT hardlimit flag if necessary
#     # How to implement this?
#     self.set_qc("DPT", "hardlimit", 0)
#     for var in ["AT", "DPT", "SHU", "RH"]:
#         if qc.hard_limit(self.getvar(var), parameters[var]["hard_limits"]) == 1:
#             self.set_qc("DPT", "hardlimit", 1)


def do_base_qc_header(
    list_of_parameters_we_need, do_first_step=False, do_last_step=False
):
    """Basic row QC for header file.

    Since we have only one QC flag in the header file:

    report_quality
    https://glamod.github.io/cdm-obs-documentation/tables/code_tables/quality_flag/quality_flag.html

    we return "1" (failed) if one test fails.
    """
    if do_first_step is True:
        flag = first_function(some_of_the_list_of_parameters_we_need)

    if flag == "1":
        return flag

    if do_last_step is True:
        flag = last_function(some_of_the_list_of_parameters_we_need)

    return flag


def do_base_qc_at(list_of_parameters_we_need, do_first_step=False, do_last_step=False):
    """Basic row QC for observation file.

    See do_base_qc_header

    We copy and adjust thgis function for each observation value (sst, slp, wbt, wd, ws)
    """
    return
