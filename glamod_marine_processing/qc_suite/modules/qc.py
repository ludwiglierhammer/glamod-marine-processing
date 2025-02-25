"""
The QC module contains a set of functions for performing the basic QC
checks on marine reports as well as some generally helpful functions
for identifying which grid box or pentad an observations falls in
"""

from __future__ import annotations

import calendar
import math
from datetime import datetime, timedelta

import numpy as np

# Conversion factor between degrees and radians
degrad = np.pi / 180.0


def month_match(y1, m1, y2, m2):
    """Check whether month matches."""
    if y1 == y2 and m1 == m2:
        return 1
    else:
        return 0


def yesterday(year, month, day):
    """'
    For specified year month and day return the year month and day of the day before.

    :param year: year
    :param month: month
    :param day: day
    :type year: integer
    :type month: integer
    :type day: integer

    :return: tuple of year, month and day, returns None if the input day does not exist (e.g. Feb 30th)
    :rtype: integer
    """
    try:
        dt = datetime(year, month, day)
        delta = timedelta(-1)
        dt = dt + delta
        return dt.year, dt.month, dt.day
    except Exception:
        return None, None, None


def season(month):
    """
    Return short season name for given month, None for months like 13 that do not exist

    :param month: month
    :type month: integer

    :return: DJF, MAM, JJA, or SON or None if the input month is non-existent (e.g. 13)
    :rtype: string
    """
    if month < 0 or month > 12:
        return None
    ssnlist = [
        "DJF",
        "DJF",
        "MAM",
        "MAM",
        "MAM",
        "JJA",
        "JJA",
        "JJA",
        "SON",
        "SON",
        "SON",
        "DJF",
    ]
    return ssnlist[month - 1]


def pentad_to_month_day(p):
    """
    Given a pentad number, return the month and day of the first day in the pentad

    :param p: pentad number from 1 to 73
    :type p: integer

    :return: month and day of the first day of the pentad
    :rtype: integer
    """
    assert 0 < p < 74, "p outside allowed range 1-73 " + str(p)
    m = [
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        6,
        6,
        6,
        6,
        6,
        6,
        7,
        7,
        7,
        7,
        7,
        7,
        8,
        8,
        8,
        8,
        8,
        8,
        9,
        9,
        9,
        9,
        9,
        9,
        10,
        10,
        10,
        10,
        10,
        10,
        11,
        11,
        11,
        11,
        11,
        11,
        12,
        12,
        12,
        12,
        12,
        12,
    ]
    d = [
        1,
        6,
        11,
        16,
        21,
        26,
        31,
        5,
        10,
        15,
        20,
        25,
        2,
        7,
        12,
        17,
        22,
        27,
        1,
        6,
        11,
        16,
        21,
        26,
        1,
        6,
        11,
        16,
        21,
        26,
        31,
        5,
        10,
        15,
        20,
        25,
        30,
        5,
        10,
        15,
        20,
        25,
        30,
        4,
        9,
        14,
        19,
        24,
        29,
        3,
        8,
        13,
        18,
        23,
        28,
        3,
        8,
        13,
        18,
        23,
        28,
        2,
        7,
        12,
        17,
        22,
        27,
        2,
        7,
        12,
        17,
        22,
        27,
    ]
    return m[p - 1], d[p - 1]


def which_pentad(inmonth, inday):
    """
    take month and day as inputs and return pentad in range 1-73.

    :param inmonth: month containing the day for which we want to calculate the pentad
    :param inday: day for the day for which we want to calculate the pentad
    :type inmonth: integer
    :type inday: integer

    :return: pentad (5-day period) containing input day, from 1 (1 Jan-5 Jan) to 73 (27-31 Dec)
    :rtype: integer

    The calculation is rather simple. It just loops through the year and adds up days till it reaches
    the day we are interested in. February 29th is treated as though it were March 1st in a regular year.
    """
    assert 12 >= inmonth >= 1
    assert 31 >= inday >= 1

    pentad = int((day_in_year(inmonth, inday) - 1) / 5)
    pentad = pentad + 1

    assert pentad >= 1
    assert pentad <= 73

    return pentad


def day_in_year(month, day):
    """
    Find the day number of a particular day from Jan 1st which is 1
    to Dec 31st which is 365.

    :param month: month to be processed
    :param day: day in the month
    :type month: integer
    :type day: integer

    :return: day number in year 1-365
    :rtype: integer
    """
    assert month >= 1
    assert month <= 12, str(month)
    month_lengths = get_month_lengths(2004)
    assert day >= 1
    assert day <= month_lengths[month - 1]
    month_lengths = get_month_lengths(2003)

    if month == 1:
        dindex = day
    elif month == 2 and day == 29:
        dindex = day_in_year(3, 1)
    else:
        dindex = np.sum(month_lengths[0 : month - 1]) + day

    return dindex


def get_hires_sst(lat, lon, month, day, hires_field):
    """
    Get a value from a high resolution ie 0.25 degree daily SST field

    :param lat: latitude of point to extract
    :param lon: longitude of point to extract
    :param month: month of point to extract
    :param day: day in month of point to extract
    :param hires_field: the field from which to extract the point
    :type lat: float
    :type lon: float
    :type month: int
    :type day: int
    :type hires_field: numpy array
    :return: the SST from the field at the specified point
    """
    assert lat >= -90.0
    assert lat <= 90.0
    assert lon >= -180.00
    assert lon <= 360.00
    assert month >= 1
    assert month <= 12
    month_lengths = get_month_lengths(2004)
    assert day >= 1
    assert day <= month_lengths[month - 1]

    dindex = day_in_year(month, day) - 1
    yindex = lat_to_yindex(lat, 0.25)
    xindex = lon_to_xindex(lon, 0.25)

    result = hires_field[dindex, 0, yindex, xindex]

    if result == -999:
        result = None

    return result


def get_sst_daily(lat, lon, month, day, sst):
    """Get SST from pentad climatology interpolated to day."""
    assert lat >= -90.0
    assert lat <= 90.0
    assert lon >= -185.00
    assert lon <= 365.00
    assert month >= 1
    assert month <= 12
    month_lengths = get_month_lengths(2004)
    assert day >= 1
    assert day <= month_lengths[month - 1]

    dindex = day_in_year(month, day) - 1
    yindex = mds_lat_to_yindex(lat)
    xindex = mds_lon_to_xindex(lon)

    result = sst[dindex, yindex, xindex]

    if type(result) is np.float64 or type(result) is np.float32:
        pass
    else:
        if result.mask:
            result = None
        else:
            result = result.data[0]

    return result


def get_sst(lat, lon, month, day, sst):
    """
    when given an array (sst) of appropriate type, extracts the value associated with that pentad,
    latitude and longitude.

    :param lat: latitude of the point
    :param lon: longitude of the point
    :param month: month of the point
    :param day: day of the point
    :param sst: an array holding the 1x1x5-day gridded values
    :type lat: float
    :type lon: float
    :type month: integer
    :type day: integer
    :type sst: numpy array
    :return: value in array at this point
    :rtype: float

    The structure of the SST array has to be quite specific it assumes a grid that is 360 x 180 x 73
    i.e. one year of 1degree lat x 1degree lon data split up into pentads. The west-most box is at 180degrees with
    index 0 and the northern most box also has index zero.
    """
    assert lat >= -90.0
    assert lat <= 90.0
    assert lon >= -185.00
    assert lon <= 365.00
    assert month >= 1
    assert month <= 12

    month_lengths = get_month_lengths(2004)

    assert day >= 1
    assert day <= month_lengths[month - 1]

    if len(sst[:, 0, 0]) == 1:
        result = get_sst_single_field(lat, lon, sst)
    else:
        # read sst from grid
        pentad = which_pentad(month, day)
        yindex = lat_to_yindex(lat)
        xindex = lon_to_xindex(lon)

        result = sst[pentad - 1, yindex, xindex]

        # sometimes this will be a numpy array and sometimes it will
        # be a masked array. Need to identify which and
        # make sure output is appropriate
        if type(result) is np.float64 or type(result) is np.float32:
            pass
        else:
            if result.mask:
                result = None
            else:
                result = result.data[0]

    return result


def get_hires_clim(rep, clim):
    """
    Get the climatological value for this particular observation

    :param rep: a MarineReport
    :param clim: a masked array containing the climatological averages
    :type rep: MarineReport
    :type clim: numpy array
    """
    try:
        rep_clim = get_hires_sst(
            rep.lat(), rep.lon(), rep.getvar("MO"), rep.getvar("DY"), clim
        )
        rep_clim = float(rep_clim)
    except Exception:
        rep_clim = None

    return rep_clim


def bilinear_interp(x1, x2, y1, y2, x, y, q11, q12, q21, q22):
    """
    Perform a bilinear interpolation at the point x,y from the rectangular grid
    defined by x1,y1 and x2,y2 with values at the four corners equal to Q11, Q12,
    Q21 and Q22.
    """
    assert x1 <= x <= x2
    assert y1 <= y <= y2
    assert x2 > x1
    assert y2 > y1
    assert q11 is not None and q12 is not None and q21 is not None and q22 is not None

    val = q11 * (x2 - x) * (y2 - y)
    val += q21 * (x - x1) * (y2 - y)
    val += q12 * (x2 - x) * (y - y1)
    val += q22 * (x - x1) * (y - y1)
    val /= (x2 - x1) * (y2 - y1)

    assert val <= 0.0001 + max([q11, q12, q21, q22]), (
        str(val) + " " + str(q11) + " " + str(q12) + " " + str(q21) + " " + str(q22)
    )
    assert val >= -0.0001 + min([q11, q12, q21, q22]), (
        str(val) + " " + str(q11) + " " + str(q12) + " " + str(q21) + " " + str(q22)
    )
    return val


def missing_mean(inarr):
    """Return mean value or None."""
    result = 0.0
    num = 0.0
    for val in inarr:
        if val is not None:
            result += val
            num += 1.0
    if num == 0.0:
        return None
    else:
        return result / num


def fill_missing_vals(q11, q12, q21, q22):
    """
    For a group of four neighbouring grid boxes which form a square,
    fill gaps using means of neighbours.
    """
    outq11 = q11
    outq12 = q12
    outq21 = q21
    outq22 = q22

    if outq11 is None:
        outq11 = missing_mean([q12, q21])
    if outq11 is None:
        outq11 = q22

    if outq22 is None:
        outq22 = missing_mean([q12, q21])
    if outq22 is None:
        outq22 = q11

    if outq12 is None:
        outq12 = missing_mean([q11, q22])
    if outq12 is None:
        outq12 = q21

    if outq21 is None:
        outq21 = missing_mean([q11, q22])
    if outq21 is None:
        outq21 = q12

    return outq11, outq12, outq21, outq22


def get_four_surrounding_points(lat, lon, max90=1):
    """Get fur surrounding points."""
    assert -90.0 <= lat <= 90.0
    assert -180.0 <= lon <= 180.0

    x2_index = lon_to_xindex(lon + 0.5)
    x2 = xindex_to_lon(x2_index)
    if x2 < lon:
        x2 += 360.0

    x1_index = lon_to_xindex(lon - 0.5)
    x1 = xindex_to_lon(x1_index)
    if x1 > lon:
        x1 -= 360.0

    if lat + 0.5 <= 90:
        y2_index = lat_to_yindex(lat + 0.5)
        y2 = yindex_to_lat(y2_index)
    else:
        y2 = 89.5
        if max90 == 0:
            y2 = 90.5

    if lat - 0.5 >= -90:
        y1_index = lat_to_yindex(lat - 0.5)
        y1 = yindex_to_lat(y1_index)
    else:
        y1 = -89.5
        if max90 == 0:
            y1 = -90.5

    return x1, x2, y1, y2


def get_clim_interpolated(rep, clim):
    """Get climatological interpolation."""
    lat = rep.lat()
    lon = rep.lon()
    mo = rep.getvar("MO")
    dy = rep.getvar("DY")

    try:
        pert1 = get_sst(lat + 0.001, lon + 0.001, mo, dy, clim)
    except Exception:
        pert1 = None
    try:
        pert2 = get_sst(lat + 0.001, lon - 0.001, mo, dy, clim)
    except Exception:
        pert2 = None
    try:
        pert3 = get_sst(lat - 0.001, lon + 0.001, mo, dy, clim)
    except Exception:
        pert3 = None
    try:
        pert4 = get_sst(lat - 0.001, lon - 0.001, mo, dy, clim)
    except Exception:
        pert4 = None
    if pert1 is None and pert2 is None and pert3 is None and pert4 is None:
        return None

    x1, x2, y1, y2 = get_four_surrounding_points(lat, lon, 1)

    try:
        q11 = get_sst(y1, x1, mo, dy, clim)
    except Exception:
        q11 = None
    if q11 is not None:
        q11 = float(q11)

    try:
        q22 = get_sst(y2, x2, mo, dy, clim)
    except Exception:
        q22 = None
    if q22 is not None:
        q22 = float(q22)

    try:
        q12 = get_sst(y2, x1, mo, dy, clim)
    except Exception:
        q12 = None
    if q12 is not None:
        q12 = float(q12)

    try:
        q21 = get_sst(y1, x2, mo, dy, clim)
    except Exception:
        q21 = None
    if q21 is not None:
        q21 = float(q21)

    q11, q12, q21, q22 = fill_missing_vals(q11, q12, q21, q22)

    x1, x2, y1, y2 = get_four_surrounding_points(lat, lon, 0)

    return bilinear_interp(x1, x2, y1, y2, lon, lat, q11, q12, q21, q22)


def get_clim(rep, clim):
    """
    Get the climatological value for this particular observation

    :param rep: a MarineReport
    :param clim: a masked array containing the climatological averages
    :type rep: MarineReport
    :type clim: numpy array
    """
    try:
        rep_clim = get_sst(
            rep.lat(), rep.lon(), rep.getvar("MO"), rep.getvar("DY"), clim
        )
        rep_clim = float(rep_clim)
    except Exception:
        rep_clim = None

    return rep_clim


def get_sst_single_field(lat, lon, sst):
    """
    when given an array (sst) of appropriate type, extracts the value associated with that pentad,
    latitude and longitude.

    :param lat: latitude of the point
    :param lon: longitude of the point
    :param sst: an array holding the 1x1x5-day gridded values
    :type lat: float
    :type lon: float
    :type sst: numpy array
    :return: value in array at this point
    :rtype: float

    The structure of the SST array has to be quite specific it assumes a grid that is 360 x 180 x 73
    i.e. one year of 1degree lat x 1degree lon data split up into pentads. The west-most box is at 180degrees with
    index 0 and the northern most box also has index zero.
    """
    assert lat >= -90.0
    assert lat <= 90.0
    assert lon >= -180.00
    assert lon <= 360.00

    # read sst from grid
    yindex = lat_to_yindex(lat)
    xindex = lon_to_xindex(lon)

    result = sst[0, yindex, xindex]

    # sometimes this will be a numpy array and sometimes it will
    # be a masked array. Need to identify which and
    # make sure output is appropriate
    if type(result) is np.float64 or type(result) is np.float32:
        pass
    else:
        if result.mask:
            result = None
        else:
            result = result.data[0]

    return result


def blacklist(inid, indeck, inyear, inmonth, inlat, inlon, inpt=1):
    """
    Blacklisting of observations from Deck 732 and others as needed

    :param inid: ID of the report
    :param indeck: Deck of the report
    :param inyear: year of the report
    :param inmonth: month of the report
    :param inlat: latitude of the report
    :param inlon: longitude of the report
    :param inpt: pentad of the report
    :type inid: string
    :type indeck: integer
    :type inyear: integer
    :type inmonth: integer
    :type inlat: float
    :type inlon: float
    :type inpt: integer

    If the report is from Deck 732, compares the observations year and location to a table of pre-identified
    regions in which Deck 732 observations are known to be dubious - see Rayner et al. 2006 and Kennedy et al.
    2011b. Observations at 0 degrees latitude 0 degrees longitude are blacklisted as this is a common error.
    C-MAN stations with platform type 13 are blacklisted. SEAS data from deck 874 are unreliable (SSTs were
    often in excess of 50degC) and so the deck was removed.
    """
    if inlon > 180.0:
        inlon -= 360

    result = 0

    if inlat == 0.0 and inlon == 0.0:
        result = 1  # blacklist all obs at 0,0

    if inpt is not None and inpt == 13:
        result = 1  # C-MAN data

    if inid == "SUPERIGORINA":
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

    if indeck == 732:
        if inyear in year_to_regions:
            regions_to_check = year_to_regions[inyear]
            for regid in regions_to_check:
                thisreg = region[regid]
                if (
                    thisreg[0] <= inlon <= thisreg[2]
                    and thisreg[1] <= inlat <= thisreg[3]
                ):
                    result = 1

    if indeck == 874:
        result = 1  # SEAS data gets blacklisted

    if (
        (inyear == 2005 and inmonth == 11)
        or (inyear == 2005 and inmonth == 12)
        or (inyear == 2006 and inmonth == 1)
    ):
        if inid in [
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


def climatology_plus_stdev_with_lowbar(inval, inclimav, instdev, limit, lowbar):
    """
    Climatology check with standard deviation-based limits but with a minimum width

    :param inval: value to be compared to climatology
    :param inclimav: the climatological average to which it will be compared
    :param instdev: the standard deviation which will be used to test the anomaly
    :param limit: maximum standardised anomaly
    :param lowbar: the anomaly must be greater than lowbar to fail regardless of standard deviation
    :return: return 1 if the difference is outside the specified range, 0 otherwise.
    """
    assert limit > 0, "multiplier must be positive and non-zero"

    result = 0
    if inval is None or inclimav is None or instdev is None:
        result = 1
    else:
        if abs(inval - inclimav) / instdev > limit and abs(inval - inclimav) > lowbar:
            result = 1

    assert result == 0 or result == 1

    return result


def climatology_plus_stdev_check(inval, inclimav, instdev, stdev_limits, limit):
    """
    Climatology check which uses standardised anomalies.

    :param inval: value to be compared to climatology
    :param inclimav: the climatological average to which the value will be compared
    :param instdev: the climatological standard deviation which will be used to standardise the anomaly
    :param stdev_limits: upper and lower limits for standard deviation used in check
    :param limit: the maximum allowed normalised anomaly
    :type inval: float
    :type inclimav: float
    :type instdev: float
    :type stdev_limits: two-membered list
    :type limit: float
    :return: return 1 if the difference is outside the specified limit, 0 otherwise (or if any input is None)
    :rtype: integer
    """
    assert stdev_limits[1] > stdev_limits[0], "limits are awry"
    assert limit > 0, "multiplier must be positive and non-zero"

    result = 0
    if inval is None or inclimav is None or instdev is None:
        result = 1
    else:
        stdev = instdev
        if stdev < stdev_limits[0]:
            stdev = stdev_limits[0]
        if stdev > stdev_limits[1]:
            stdev = stdev_limits[1]

        if abs(inval - inclimav) / stdev > limit:
            result = 1

    assert result == 0 or result == 1

    return result


def climatology_check(inval, inclimav, limit=8.0):
    """
    Simple function to compare a value with a climatological average with some arbitrary limit on the difference

    :param inval: value to be compared to climatology
    :param inclimav: the climatological average to which the value will be compared
    :param limit: the maximum allowed difference between the two
    :type inval: float
    :type inclimav: float
    :type limit: float
    :return: return 1 if the difference is outside the specified limit, 0 otherwise
    :rtype: integer

    This may be the second simplest function I have ever written (see blacklist)
    """
    result = 0

    if inval is None or inclimav is None or limit is None:
        result = 1
    else:
        if abs(inval - inclimav) > limit:
            result = 1

    assert result == 0 or result == 1

    return result


def value_check(inval):
    """
    Check if a value is equal to None

    :param inval: the input value
    :param inval: float
    :return: 1 if the input value is None, 0 otherwise
    :return type: integer
    """
    result = 0
    if inval is None:
        result = 1
    return result


def no_normal_check(inclimav):
    """
    Check if a climatological average is equal to None

    :param inclimav: the input value
    :type inclimav: float
    :return: 1 if the input value is None, 0 otherwise
    :return type: integer
    """
    result = 0
    if inclimav is None:
        result = 1
    return result


def hard_limit(val, limits):
    """
    Check if a value is outside specified limits

    :param val: value to be tested
    :param limits: two membered list of lower and upper limit
    :type val: float
    :type limits: list of floats

    :return: 1 if the input is outside the limits, 0 otherwise
    :return type: integer
    """
    assert limits[1] > limits[0], "limits are not well specified"
    if val is None:
        return 1
    result = 1
    if limits[0] <= val <= limits[1]:
        result = 0
    return result


def supersat_check(invaltd, invalt):
    """
    Check if a valid dewpoint temperature is
    greater than a valid air temperature

    :param invaltd: the input value for dewpoint temperature
    :param invalt: the input value for air temperature
    :type invaltd: float
    :type invalt: float
    :return: 1 if the input values are invalid/None
    :return: 1 if the dewpoint temperature is greater than the air temperarture
    :return: 0 otherwise
    :return type: integer
    """
    result = 0
    if (invaltd is None) | (invalt is None):
        result = 1
    elif invaltd > invalt:
        result = 1

    return result


def sst_freeze_check(insst, sst_uncertainty=0.0, freezing_point=-1.80, n_sigma=2.0):
    """
    Compare an input SST to see if it is above freezing.

    :param insst: the input SST
    :param sst_uncertainty: the uncertainty in the SST value, defaults to zero
    :param freezing_point: the freezing point of the water, defaults to -1.8C
    :param n_sigma: number of sigma to use in the check
    :type insst: float
    :type sst_uncertainty: float
    :type freezing_point: float
    :type n_sigma: float
    :return: 1 if the input SST is below freezing point by more than twice the uncertainty, 0 otherwise
    :return type: integer

    This is a simple freezing point check made slightly more complex. We want to check if a
    measurement of SST is above freezing, but there are two problems. First, the freezing point
    can vary from place to place depending on the salinity of the water. Second, there is uncertainty
    in SST measurements. If we place a hard cut-off at -1.8, then we are likely to bias the average
    of many measurements too high when they are near the freezing point - observational error will
    push the measurements randomly higher and lower, and this test will trim out the lower tail, thus
    biasing the result. The inclusion of an SST uncertainty parameter *might* mitigate that.
    """
    assert sst_uncertainty is not None and freezing_point is not None

    # fail if SST below the freezing point by more than twice the uncertainty
    result = 0
    if insst is not None:
        if insst < (freezing_point - n_sigma * sst_uncertainty):
            result = 1

    assert result == 1 or result == 0
    return result


def position_check(inlat, inlon):
    """
    Simple check to make sure that the latitude and longitude are within the bounds specified
    by the ICOADS documentation. Latitude is between -90 and 90. Longitude is between -180 and 360

    :param inlat: latitude
    :param inlon: longitude
    :type inlat: float
    :type inlon: float
    :return: 1 if either latitude or longitude is invalid, 0 otherwise
    :return type: integer
    """
    # return 1 if lat or lon is invalid, 0 otherwise
    assert inlat is not None and not (math.isnan(inlat))
    assert inlon is not None and not (math.isnan(inlon))
    result = 0
    if inlat < -90 or inlat > 90:
        result = 1
    if inlon < -180 or inlon > 360:
        result = 1
    assert result == 1 or result == 0
    return result


def time_check(inhour):
    """
    Check that the time is valid

    :param inhour: hour of the time to be checked
    :type inhour: float
    :return: 1 if the hour is invalid, 0 otherwise
    :return type: integer
    """
    result = 0

    if inhour is not None and (inhour >= 24 or inhour < 0):
        result = 1

    if inhour is None:
        result = 1

    return result


def date_check(inyear, inmonth, inday):
    """
    Check that the date is valid

    :param inyear: year of the date to be checked
    :param inmonth: month of the data to be checked
    :param inday: day of the date to be checked
    :type inyear: integer
    :type inmonth: integer
    :type inday: integer
    :return: 1 if any one of the inputs (or the combined inputs) is invalid, 0 otherwise
    :return type: integer
    """
    # return 1 if date is valid. 0 otherwise
    assert inyear is not None
    assert inmonth is not None

    result = 0

    if inyear > 2024 or inyear < 1850:
        result = 1

    if inmonth < 1 or inmonth > 12:
        result = 1

    month_lengths = get_month_lengths(inyear)

    if inday is None:
        result = 1
    else:
        if inday < 1 or inday > month_lengths[inmonth - 1]:
            result = 1

    return result


def wind_consistency(windspeed, winddirection, variablelimit):
    """
    Test to compare windspeed to winddirection.
    :param windspeed:  wind speed
    :param winddirection: wind direction in range 1-362
    :param variablelimit: maximum wind speed consistent with variable wind direction
    :type windspeed: float
    :type winddirection: integer
    :type variablelimit: float
    :return: pass (0) or fail (1)
    :rtype: integer
    """
    result = 0

    if winddirection is None or windspeed is None:
        result = 1
    else:
        # direction 361 is Calm i.e. windspeed should be zero
        if winddirection == 361 and windspeed != 0:
            result = 1

        # direction 363 is Variable i.e. low windspeed
        if winddirection == 362 and windspeed > variablelimit:
            result = 1

    return result


def p_data_given_good(x, q, r_hi, r_lo, mu, sigma):
    """
    Calculate the probability of an observed value x given a normal distribution with mean mu
    standard deviation of sigma, where x is constrained to fall between R_hi and R_lo
    and is known only to an integer multiple of Q, the quantization level.

    :param x: observed value for which probability is required
    :param q: quantization of x, i.e. x is an integer multiple of Q
    :param r_hi: the upper limit on x imposed by previous QC choices.
    :param r_lo: the lower limit on x imposed by previous QC choices.
    :param mu: the mean of the distribution.
    :param sigma: the standard deviation of the distribution
    :type x: float
    :type q: float
    :type r_hi: float
    :type r_lo: float
    :type mu: float
    :type sigma: float
    :return: probability of the observed value given the specified distribution.
    :rtype: float
    """
    assert q > 0.0, "q <= 0" + str(q)
    assert sigma > 0.0, "sigma <= 0 " + str(sigma)
    assert r_hi > r_lo, (
        "Limits not ascending r_lo " + str(r_lo) + " > r_hi " + str(r_hi)
    )
    assert x >= r_lo, "x below lower limit " + str(x) + " < r_lo " + str(r_lo)
    assert x <= r_hi, "x above upper limit " + str(x) + " > r_hi " + str(r_hi)

    upper_x = min([x + 0.5 * q, r_hi + 0.5 * q])
    lower_x = max([x - 0.5 * q, r_lo - 0.5 * q])

    normalizer = 0.5 * (
        math.erf((r_hi + 0.5 * q - mu) / (sigma * math.sqrt(2)))
        - math.erf((r_lo - 0.5 * q - mu) / (sigma * math.sqrt(2)))
    )

    return (
        0.5
        * (
            math.erf((upper_x - mu) / (sigma * math.sqrt(2)))
            - math.erf((lower_x - mu) / (sigma * math.sqrt(2)))
        )
        / normalizer
    )


def p_data_given_gross(q, r_hi, r_lo):
    """
    Calculate the probability of the data given a gross error
    assuming gross errors are uniformly distributed between
    R_low and R_high and that the quantization, rounding level is Q

    :param q: quantization of x, i.e. x is an integer multiple of Q
    :param r_hi: the upper limit on x imposed by previous QC choices.
    :param r_lo: the lower limit on x imposed by previous QC choices.
    :type q: float
    :type r_hi: float
    :type r_lo: float
    :return: probability of the observed value given that its a gross error.
    :rtpye: float
    """
    assert r_hi > r_lo, (
        "Limits not ascending r_lo " + str(r_lo) + " > r_hi " + str(r_hi)
    )
    assert q > 0.0, "q <= 0" + str(q)

    r = r_hi - r_lo
    return 1.0 / (1.0 + (r / q))


def p_gross(p0, q, r_hi, r_lo, x, mu, sigma):
    """
    Calculate the posterior probability of a gross error given the prior probability p0,
    the quantization level of the observed value, Q, previous limits on the observed value,
    R_hi and R_lo, the observed value, x, and the mean (mu) and standard deviation (sigma) of the
    distribution of good observations assuming they are normally distributed. Gross errors are
    assumed to be uniformly distributed between R_lo and R_hi.

    :param p0: prior probability of gross error
    :param q: quantization of x, i.e. x is an integer multiple of Q
    :param r_hi: the upper limit on x imposed by previous QC choices.
    :param r_lo: the lower limit on x imposed by previous QC choices.
    :param x: observed value for which probability is required
    :param mu: the mean of the distribution of good obs.
    :param sigma: the standard deviation of the distribution of good obs
    :type q: float
    :type r_hi: float
    :type r_lo: float
    :return: probability of gross error given an observed value
    :rtpye: float
    """
    assert p0 >= 0, "p0 <= 0 " + str(p0)
    assert p0 <= 1, "p0 > 1 " + str(p0)
    assert q > 0.0, "q <= 0 " + str(q)
    assert r_hi > r_lo, (
        "Limits not ascending r_lo " + str(r_lo) + " > r_hi " + str(r_hi)
    )
    assert x >= r_lo, "x below lower limit " + str(x) + " < r_lo " + str(r_lo)
    assert x <= r_hi, "x above upper limit " + str(x) + " > r_hi " + str(r_hi)
    assert sigma > 0.0, "sigma <= 0 " + str(sigma)

    pgross = (
        p0
        * p_data_given_gross(q, r_hi, r_lo)
        / (
            p0 * p_data_given_gross(q, r_hi, r_lo)
            + (1 - p0) * p_data_given_good(x, q, r_hi, r_lo, mu, sigma)
        )
    )

    assert pgross >= 0.0, pgross
    assert pgross <= 1.0, pgross

    return pgross


def angle_diff(angle1, angle2):
    """
    Calculate the angular distance on a circle between two points given in radians

    :param angle1: angle of first point
    :param angle2: angle of second point
    :type angle1: float
    :type angle2: float
    :return: angle between the two input points in radians
    :return type: float
    """
    assert angle1 is not None and angle2 is not None
    # calculate angle between two angles
    diff = abs(angle1 - angle2)
    if diff > np.pi:
        diff = 2.0 * np.pi - diff
    return diff


def relative_year_number(year, reference=1979):
    """Get number of year relative to reference year."""
    return year - (reference + 1)


def convert_time_in_hours(hour, minute, sec, zone, dasvtm):
    """Convert to time in hours."""
    return hour + (minute + sec / 60.0) / 60.0 + zone - dasvtm


def leap_year(delyear):
    """Get leap year."""
    return math.floor(delyear / 4.0)


def time_in_whole_days(time_in_hours, day, delyear, leap):
    """Calculate from time in hours to time in whole days."""
    return delyear * 365 + leap + day - 1.0 + time_in_hours / 24.0


def leap_year_correction(time_in_hours, day, delyear):
    """Make eap year correction."""
    leap = leap_year(delyear)
    time = time_in_whole_days(time_in_hours, day, delyear, leap)
    if delyear == leap * 4.0:
        time = time - 1.0
    if delyear < 0 and delyear != leap * 4.0:
        time = time - 1.0
    return time


def sun_position(time):
    """Find position of sun in celestial sphere, assuming circular orbit (radians)."""
    return (360.0 * time / 365.25) * degrad


def mean_earth_anomaly(time, theta):
    """Calculate mean anomaly of earth (g)."""
    return -0.031271 - 4.5396e-7 * time + theta


def sun_longitude(time):
    """Get longitude of sun."""
    theta = sun_position(time)
    mean_anomaly = mean_earth_anomaly(time, theta)
    return (
        4.900968
        + 3.6747e-7 * time
        + (0.033434 - 2.3e-9 * time) * math.sin(mean_anomaly)
        + 0.000349 * math.sin(2.0 * mean_anomaly)
        + theta
    )


def elliptic_angle(time):
    """Get angle plane of elliptic to plane of celestial equator."""
    return 0.409140 - 6.2149e-9 * time


def sun_ascension(long_of_sun, sin_long_of_sun, angle_of_elliptic):
    """Calculate right ascension."""
    a1 = sin_long_of_sun * math.cos(angle_of_elliptic)
    a2 = math.cos(long_of_sun)
    right_ascension = math.atan2(a1, a2)
    if right_ascension < 0.0:
        right_ascension = right_ascension + 2 * np.pi
    return right_ascension


def sun_declination(sin_long_of_sun, angle_of_elliptic):
    """Calculate declination of sun."""
    return math.asin(sin_long_of_sun * math.sin(angle_of_elliptic))


def calculate_sun_parameters(time):
    """Calculate both right ascension and declination of sun."""
    long_of_sun = sun_longitude(time)
    angle_of_elliptic = elliptic_angle(time)
    sin_long_of_sun = math.sin(long_of_sun)
    rta = sun_ascension(long_of_sun, sin_long_of_sun, angle_of_elliptic)
    dec = sun_declination(sin_long_of_sun, angle_of_elliptic)
    return rta, dec


def to_siderial_time(time, delyear):
    """Convert to siderial time."""
    sid = 1.759335 + 2 * np.pi * (time / 365.25 - delyear) + 3.694e-7 * time
    if sid >= 2 * np.pi:
        sid = sid - 2 * np.pi
    return sid


def to_local_siderial_time(time, time_in_hours, delyear, lon):
    """Convert to local siderial time.."""
    siderial_time = to_siderial_time(time, delyear)
    lsid = siderial_time + (time_in_hours * 15.0 + lon) * degrad
    if lsid >= 2 * np.pi:
        lsid = lsid - 2 * np.pi
    return lsid


def sun_hour_angle(local_siderial_time, right_ascension):
    """Get hour angle."""
    hra = local_siderial_time - right_ascension
    if hra < 0:
        hra = hra + 2 * np.pi
    return hra


def sin_of_elevation(phi, declination, hour_angle):
    """Get sinus of geometric elevation."""
    sin_elevation = math.sin(phi) * math.sin(declination) + math.cos(phi) * math.cos(
        declination
    ) * math.cos(hour_angle)
    if sin_elevation > 1.0:
        sin_elevation = 1.0
    if sin_elevation < -1.0:
        sin_elevation = -1.0
    return sin_elevation


def sun_azimuth(phi, declination):
    """Get azimuth."""
    if (phi - declination) > 0:
        return 0
    else:
        return 180


def convert_degrees(deg):
    """Convert drgrees."""
    if deg < 0.0:
        deg = 360.0 + deg
    return deg


def calculate_azimuth(declination, hour_angle, elevation, phi):
    """Calculate azimuth."""
    val_to_asin = math.cos(declination) * math.sin(hour_angle) / math.cos(elevation)
    if val_to_asin > 1.0:
        val_to_asin = 1.0
    if val_to_asin < -1.0:
        val_to_asin = -1.0
    azimuth = math.asin(val_to_asin) / degrad
    if math.sin(elevation) < math.sin(declination) / math.sin(phi):
        azimuth = convert_degrees(azimuth)
        azimuth = azimuth - 180.0
    return 180.0 + azimuth


def azimuth_elevation(lat, declination, hour_angle):
    """Get both azimuth and geometric elevation of sun."""
    phi = lat * degrad
    sin_elevation = sin_of_elevation(phi, declination, hour_angle)
    elevation = math.asin(sin_elevation)
    azimuth = sun_azimuth(phi, declination)
    # If sun is not very near the zenith, leave a as 0 or 180
    if abs(elevation - 2 * np.pi / 4.0) > 0.000001:
        # Protect against rounding error near +/-90 degrees.
        azimuth = calculate_azimuth(declination, hour_angle, elevation, phi)
    return azimuth, elevation


def sunangle(year, day, hour, minute, sec, zone, dasvtm, lat, lon):
    """
    Calculate the local azimuth and elevation of the sun at a specified location and time.

    :param year: year number
    :param day: day number of year starting with 1 for Jan 1st and running up to 365/6
    :param hour: hour
    :param minute: minute
    :param sec: second
    :param zone: the local international time zone, counted westward from Greenwich
    :param dasvtm: 1 if daylight saving time is in effect, otherwise 0
    :param lat: latitude in degrees, north is positive
    :param lon: longitude in degrees, east is positive
    :type year: integer
    :type day: integer
    :type hour: integer
    :type minute: integer
    :type sec: integer
    :type zone: integer
    :type dasvtm: integer
    :type lat: float
    :type lon: float

    :return:  Azimuth angle of the sun (degrees east of north), Elevation of sun (degrees),
              Right ascension of sun (degrees), Hour angle of sun (degrees), Hour angle of
              local siderial time (degrees), Declination of sun (degrees)
    :rtype: float

    Copied from Rob Hackett's area 28 Apr 1998 by J.Arnott.
    Add protection for ASIN near +/- 90 degrees 07 Jan 2002 by J.Arnott.
    Pythonised 25/09/2015 by J.J. Kennedy

    The Python version gets within a fraction of a degree of the original Fortran code from which it was ported
    for a range of values. The differences are larger if single precision values are used suggesting that this
    is not the most numerically robust scheme.
    """
    assert 0 < day <= 366
    assert 0 <= hour < 24
    assert 0 <= minute < 60
    assert 0 <= sec < 60
    assert 90 >= lat >= -90

    # Find number of whole years since end of 1979 (reference point)
    delyear = relative_year_number(year)
    # Find time in whole hours since midnight (allow for "daylight saving").
    time_in_hours = convert_time_in_hours(hour, minute, sec, zone, dasvtm)
    # Make leap year correction
    time = leap_year_correction(time_in_hours, day, delyear)
    # Get sun parameters
    right_ascension, declination = calculate_sun_parameters(time)
    local_siderial_time = to_local_siderial_time(time, time_in_hours, delyear, lon)
    # Hour Angle
    hour_angle = sun_hour_angle(local_siderial_time, right_ascension)
    # Geometric elevation and sun azimuth
    azimuth, elevation = azimuth_elevation(lat, declination, hour_angle)

    elevation = elevation / degrad  # Convert elevation to degrees
    declination = declination / degrad  # Convert declination to degrees

    assert 180 >= elevation >= -180

    rta = right_ascension / degrad
    sid = local_siderial_time / degrad
    sid = convert_degrees(sid)
    hra = hour_angle / degrad
    hra = convert_degrees(hra)

    return azimuth, elevation, rta, hra, sid, declination


def dayinyear(year, month, day):
    """
    Calculate the day in year, running from 1 for Jan 1st to 365 (or 366) for Dec 31st

    :param year: Year
    :param month: Month
    :param day: Day
    :type year: integer
    :type month: integer
    :type day: integer
    :return: day in year, between 1 and 366
    :rtype: integer
    """
    assert 1 <= month <= 12
    assert day >= 1

    month_lengths = get_month_lengths(year)

    assert day <= month_lengths[month - 1], "Day out of range " + str(day)

    result = day
    if month > 1:
        result = result + sum(month_lengths[0 : month - 1])

    assert 1 <= result <= 366
    return result


def day_test(year, month, day, hour, lat, lon, time_since_sun_above_horizon=1.0):
    """
    Given year month day hour lat and long calculate if the sun was above the horizon an hour ago.

    :param year: Year
    :param month: Month
    :param day: Day
    :param hour: Hour
    :param lat: Latitude in degrees
    :param lon: Longitude in degrees
    :param time_since_sun_above_horizon: time since sun was above horizon for test
    :type year: integer
    :type month: integer
    :type day: integer
    :type hour: integer
    :type lat: float
    :type lon: float
    :type time_since_sun_above_horizon: float
    :return: 1 if the sun was above the horizon an hour ago, 0 otherwise.

    This is the "day" test used to decide whether a Marine Air Temperature (MAT) measurement is
    a Night MAT (NMAT) or a Day (MAT). This is important because solar heating of the ship biases
    the MAT measurements. It uses the function sunangle to calculate the elevation of the sun.
    """
    assert 1 <= month <= 12
    assert 1 <= day <= 31
    assert 0 <= hour <= 24
    assert 90 >= lat >= -90
    # hour expressed as decimal fractions of 24 hour day.
    # lat and lon in degrees
    # return 0 for night
    # return 1 for day

    result = 0

    if year is not None and month is not None and day is not None and hour is not None:
        year2 = year
        day2 = dayinyear(year, month, day)
        hour2 = math.floor(hour)
        minute2 = (hour - math.floor(hour)) * 60.0

        # go back one hour and test if the sun was above the horizon
        hour2 = hour2 - time_since_sun_above_horizon
        if hour2 < 0:
            hour2 = hour2 + 24.0
            day2 = day2 - 1
            if day2 <= 0:
                year2 = year2 - 1
                day2 = dayinyear(year2, 12, 31)

        lat2 = lat
        lon2 = lon
        if lat == 0:
            lat2 = 0.0001
        if lon == 0:
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
            result = 1

    assert result == 1 or result == 0
    return result


def jul_day(year, month, day):
    """
    Routine to calculate julian day. This is the weird Astronomical thing which counts from 1 Jan 4713 BC.

    :param year: Year
    :param month: Month
    :param day: Day
    :type year: integer
    :type month: integer
    :type day: integer
    :return: julian day
    :rtype: integer

    This is one of those routines that looks baffling but works. No one is sure exactly how. It gets
    written once and then remains untouched for centuries, mysteriously working.
    """
    assert 1 <= month <= 12
    assert 1 <= day <= 31
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def time_difference(year1, month1, day1, hour1, year2, month2, day2, hour2):
    """
    Calculate time difference in hours between any two times

    :param year1: Year of first time point
    :param month1: Month of first time point
    :param day1: Day of first time point
    :param hour1: Hour of first time point
    :param year2: Year of second time point
    :param month2: Month of second time point
    :param day2: Day of second time point
    :param hour2: Hour of second time point
    :type year1: integer
    :type month1: integer
    :type day1: integer
    :type hour1: float
    :type year2: integer
    :type month2: integer
    :type day2: integer
    :type hour2: float
    :return: difference in hours between the two times
    :rtype: float
    """
    # return time difference in hours
    if None in [year1, year2, month1, month2, day1, day2, hour1, hour2]:
        return

    assert 0 <= hour1 < 24 and 0 <= hour2 < 24

    if (
        (year1 > year2)
        or (year1 == year2 and month1 > month2)
        or (year1 == year2 and month1 == month2 and day1 > day2)
        or (year1 == year2 and month1 == month2 and day1 == day2 and hour1 > hour2)
    ):
        return -1 * time_difference(
            year2, month2, day2, hour2, year1, month1, day1, hour1
        )

    first_day = jul_day(year1, month1, day1) + hour1 / 24.0
    last_day = jul_day(year2, month2, day2) + hour2 / 24.0

    timdif = 24.0 * (last_day - first_day)

    return timdif


def winsorised_mean(inarr):
    """
    The winsorised mean is a resistant way of calculating an average.

    :param inarr: input array to be averaged
    :type inarr: List[float]
    :return: the winsorised mean of the input array with a 25% trimming
    :rtype: float

    The winsorised mean is that which you get if you set the first quarter of
    the sorted input array to the 1st quartile value and the the last quarter
    to the 3rd quartile and then take the mean. This is quite a heavy trimming of
    the distribution. It makes it very resistant - about half the obs can be egregiously
    bad without affecting the mean strongly - but it will be less accurate if
    there are lots of observations, or the quality of the obs is higher.
    """
    length = len(inarr)

    total = 0
    lower = 0
    upper = length - 1

    inarr.sort()

    if length >= 4:
        lower = length / 4
        upper = upper - lower
        total = total + (inarr[lower] + inarr[upper]) * lower

    for j in range(lower, upper + 1):
        total += inarr[j]

    return total / length


def trimmed_mean(inarr, trim):
    """
    Calculate a resistant (aka robust) mean of an input array given a trimming criteria.

    :param inarr: list of numbers
    :param trim: trimming criteria. A value of 10 trims one tenth of the values off each end of the sorted array before
        calculating the mean.
    :type inarr: list of floats
    :type trim: integer
    :return: trimmed mean
    :rtype: float
    """
    if trim == 0:
        return np.mean(inarr)

    length = len(inarr)
    inarr.sort()

    index1 = length / trim

    trim = np.mean(inarr[index1 : length - index1])

    return trim


def yindex_to_lat(yindex, res=1):
    """Convert yindex to latitude."""
    assert yindex >= 0
    assert yindex < 180 / res
    lat = 90.0 - yindex * res - res / 2.0
    return lat


def mds_lat_to_yindex(lat, res=1.0):
    """
    For a given latitude return the y-index as it was in MDS2/3 in a 1x1 global grid

    :param lat: Latitude of the point
    :param res: resolution of grid in degrees
    :type lat: float
    :type res: float
    :return: grid box index
    :rtype: integer

    In the northern hemisphere, borderline latitudes which fall on grid boundaries are pushed north, except
    90 which goes south. In the southern hemisphere, they are pushed south, except -90 which goes north.
    At 0 degrees they are pushed south.

    Expects that latitudes run from 90N to 90S
    """
    lat_local = lat  # round(lat,1)

    if lat_local == -90:
        lat_local += 0.001
    if lat_local == 90:
        lat_local -= 0.001

    if lat > 0.0:
        return int(90 / res - 1 - int(lat_local / res))
    else:
        return int(90 / res - int(lat_local / res))

    pass


def lat_to_yindex(lat, res=1):
    """
    For a given latitude return the y index in a 1x1x5-day global grid

    :param lat: Latitude of the point
    :param res: resolution of the grid
    :type lat: float
    :type res: float
    :return: grid box index
    :rtype: integer

    The routine assumes that the structure of the SST array is a grid that is 360 x 180 x 73
    i.e. one year of 1degree lat x 1degree lon data split up into pentads. The west-most box is at 180degrees with
    index 0 and the northern most box also has index zero. Inputs on the border between grid cells are pushed south.
    """
    if res == 1:
        yindex = int(90 - lat)
        if yindex >= 180:
            yindex = 179
        if yindex < 0:
            yindex = 0
        return yindex
    else:
        yindex = int((90 - lat) / res)
        if yindex >= 180 / res:
            yindex = int(180 / res - 1)
        if yindex < 0:
            yindex = 0
        return yindex


def xindex_to_lon(xindex, res=1):
    """Convert xindex to longitude."""
    assert xindex >= 0
    assert xindex < 360 / res
    lon = xindex * res - 180.0 + res / 2.0
    return lon


def mds_lon_to_xindex(lon, res=1.0):
    """
    For a given longitude return the x-index as it was in MDS2/3 in a 1x1 global grid

    :param lon: Longitude of the point
    :param res: resolution of the field
    :type lon: float
    :type res: float
    :return: grid box index
    :rtype: integer

    In the western hemisphere, borderline longitudes which fall on grid boundaries are pushed west, except
    -180 which goes east. In the eastern hemisphere, they are pushed east, except 180 which goes west.
    At 0 degrees they are pushed west.
    """
    long_local = lon  # round(lon,1)

    if long_local == -180:
        long_local += 0.001
    if long_local == 180:
        long_local -= 0.001
    if long_local > 0.0:
        return int(int(long_local / res) + 180 / res)
    else:
        return int(int(long_local / res) + 180 / res - 1)


def lon_to_xindex(lon, res=1):
    """
    For a given longitude return the x index in a 1x1x5-day global grid

    :param lon: Longitude of the point
    :param res: resolution of the grid
    :type lon: float
    :type res: float
    :return: grid box index
    :rtype: integer

    The routine assumes that the structure of the SST array is a grid that is 360 x 180 x 73
    i.e. one year of 1degree lat x 1degree lon data split up into pentads. The west-most box is at 180degrees W with
    index 0 and the northern most box also has index zero. Inputs on the border between grid cells are pushed east.
    """
    if res == 1:
        inlon = lon
        if inlon >= 180.0:
            inlon = -180.0 + (inlon - 180.0)
        if inlon < -180.0:
            inlon = inlon + 360.0
        xindex = int(inlon + 180.0)
        while xindex >= 360:
            xindex -= 360
        return int(xindex)
    else:
        inlon = lon
        if inlon >= 180.0:
            inlon = -180.0 + (inlon - 180.0)
        if inlon < -180.0:
            inlon = inlon + 360.0
        xindex = int((inlon + 180.0) / res)
        while xindex >= 360 / res:
            xindex -= 360 / res
        return int(xindex)


def id_is_generic(inid, inyear):
    """
    Test to see if an ID is one of the generic IDs

    :param inid: ID from marine report
    :param inyear: year we are checking for
    :type inid: string
    :type inyear: integer
    :return: True if the ID is generic and False otherwise
    :rtype: logical

    Certain callsigns are shared by large numbers of ships. e.g. SHIP, PLAT, 0120,
    MASK, MASKSTID. This simple routine has a list of known generic call signs.
    Some call signs are only generic between certain years.
    """
    generic_ids = [
        None,
        "",
        " ",
        "1        ",
        "58       ",
        "RIGG     ",
        "     RIGG",
        "SHIP     ",
        "ship     ",
        "     SHIP",
        "PLAT     ",
        "     PLAT",
        "         ",
        "0120     ",
        "0204     ",
        "0205     ",
        "0206     ",
        "0207     ",
        "0208     ",
        "0209     ",
        "MASKST   ",
        "MASKSTID ",
        "MASK     ",
        "XXXX     ",
        "/////    ",
    ]

    if 1921 <= inyear <= 1941:
        generic_ids.append("2        ")
        generic_ids.append("00002    ")

    if 1930 <= inyear <= 1937:
        generic_ids.append("3        ")

    if 1934 <= inyear <= 1954:
        generic_ids.append("7        ")
        generic_ids.append("00007    ")

    result = False
    if inid in generic_ids:
        result = True
    return result


def last_month_was(year, month):
    """
    Short function to get the previous month given a particular month of interest

    :param year: year of interest
    :param month: month of interest
    :type year: integer
    :type month: integer
    """
    last_year = year
    last_month = month - 1
    if last_month == 0:
        last_month = 12
        last_year = year - 1

    return last_year, last_month


def next_month_is(year, month):
    """
    Short function to get the next month given a particular month of interest

    :param year: year of interest
    :param month: month of interest
    :type year: integer
    :type month: integer
    """
    next_year = year
    next_month = month + 1
    if next_month > 12:
        next_month = 1
        next_year = year + 1

    return next_year, next_month


def year_month_gen(year1, month1, year2, month2):
    """
    A generator to loop one month at a time between
    year1 month1 and year2 month2

    :param year1: first year to loop from
    :param month1: month in first year to start from
    :param year2: Last year to loop over
    :param month2: last month in last year to loop over
    :type year1: integer
    :type month1: integer
    :type year2: integer
    :type month2: integer
    :return: Return an iterator that yields tuples of a year and month
    :rtype: Iterator[integer]
    """
    assert year2 >= year1, "Start year after end year"
    assert 0 < month1 <= 12, "Month outside 1-12"

    year = year1
    month = month1

    while not (year == year2 and month == month2):
        yield year, month
        month += 1
        if month > 12:
            month = 1
            year += 1

    yield year, month


def get_month_lengths(year):
    """
    Return a list holding the lengths of the months in a given year

    :param year: Year for which you want month lengths
    :type year: int
    :return: list of month lengths
    :rtype: int
    """
    if calendar.isleap(year):
        month_lengths = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else:
        month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    return month_lengths


def base_qc_report(rep):
    """Take a marine report and do some base qc on it."""
    # Basic positional QC
    if rep.getvar("PT") in [6, 7]:
        rep.set_qc("POS", "isbuoy", 1)
    else:
        rep.set_qc("POS", "isbuoy", 0)

    if rep.getvar("PT") in [0, 1, 2, 3, 4, 5, 10, 11, 12, 17]:
        rep.set_qc("POS", "isship", 1)
    else:
        rep.set_qc("POS", "isship", 0)

    # See Kent et al. HadNMAT2 QC section
    rep.set_qc("POS", "mat_blacklist", 0)
    if rep.getvar("PT") == 5 and rep.getvar("DCK") == 780:
        rep.set_qc("POS", "mat_blacklist", 1)

    # make sure lons are in range -180 to 180
    lon = rep.lon()
    lat = rep.lat()
    # North Atlantic, Suez and indian ocean to be excluded from MAT processing
    if (
        rep.getvar("DCK") == 193
        and 1880 <= rep.getvar("YR") <= 1893
        and (
            (-80.0 <= lon <= 0.0 and 40.0 <= lat <= 55.0)
            or (-10.0 <= lon <= 30.0 and 35.0 <= lat <= 45.0)
            or (15.0 <= lon <= 45.0 and -10.0 <= lat <= 40.0)
            or (15.0 <= lon <= 95.0 and lat >= -10.0 and lat <= 15.0)
            or (95.0 <= lon <= 105.0 and -10.0 <= lat <= 5.0)
        )
    ):
        rep.set_qc("POS", "mat_blacklist", 1)

    if rep.getvar("DCK") == 780:
        rep.set_qc("POS", "is780", 1)
    else:
        rep.set_qc("POS", "is780", 0)

    rep.set_qc("POS", "pos", position_check(rep.lat(), rep.lon()))

    rep.set_qc(
        "POS", "date", date_check(rep.getvar("YR"), rep.getvar("MO"), rep.getvar("DY"))
    )

    if rep.get_qc("POS", "pos") == 0 and rep.get_qc("POS", "date") == 0:
        rep.set_qc(
            "POS",
            "day",
            day_test(
                rep.getvar("YR"),
                rep.getvar("MO"),
                rep.getvar("DY"),
                rep.getvar("HR"),
                rep.lat(),
                rep.lon(),
            ),
        )
    else:
        rep.set_qc("POS", "day", 1)

    rep.set_qc(
        "POS",
        "blklst",
        blacklist(
            rep.getvar("ID"),
            rep.getvar("DCK"),
            rep.getvar("YR"),
            rep.getvar("MO"),
            rep.lat(),
            rep.lon(),
            rep.getvar("PT"),
        ),
    )

    # SST base QC
    rep.set_qc("SST", "noval", value_check(rep.getvar("SST")))
    rep.set_qc("SST", "freez", sst_freeze_check(rep.getvar("SST"), 0.0))
    rep.set_qc(
        "SST", "clim", climatology_check(rep.getvar("SST"), rep.getnorm("SST"), 8.0)
    )
    rep.set_qc("SST", "nonorm", no_normal_check(rep.getnorm("SST")))

    # MAT base QC
    rep.set_qc("AT", "noval", value_check(rep.getvar("AT")))
    rep.set_qc(
        "AT", "clim", climatology_check(rep.getvar("AT"), rep.getnorm("AT"), 10.0)
    )
    rep.set_qc("AT", "nonorm", no_normal_check(rep.getnorm("AT")))

    return rep
