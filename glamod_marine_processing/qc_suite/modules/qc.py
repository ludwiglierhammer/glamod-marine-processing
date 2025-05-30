"""The QC module contains a set of functions for performing the basic QC checks on marine reports."""

from __future__ import annotations

from .auxiliary import isvalid

passed = 0
failed = 1
untestable = 2
untested = 3


def climatology_check(
    value: float,
    climate_normal: float,
    maximum_anomaly: float,
    standard_deviation: float | None = 1.0,
    standard_deviation_limits: tuple[float, float] | None = None,
    lowbar: float | None = None,
) -> int:
    """
    Climatology check to compare a value with a climatological average with some arbitrary limit on the difference.
    This check can be expanded with some optional parameters.

    Parameters
    ----------
    value: float
        Value to be compared to climatology
    climate_normal : float
        The climatological average to which it will be compared
    maximum_anomaly: float
        Largest allowed anomaly.
        If ``standard_deviation`` is provided, this is the largest allowed standardised anomaly.
    standard_deviation: float, default: 1.0
        The standard deviation which will be used to standardize the anomaly
    standard_deviation_limits: tuple of float, optional
        A tuple of two floats representing the upper and lower limits for standard deviation used in check
    lowbar: float, optional
        The anomaly must be greater than lowbar to fail regardless of standard deviation.

    Returns
    -------
    int
        2 if stdev_limits[1] is equal or less than stdev_limits[0] or
        if limit is equal or less than 0 or
        if either value, climate_normal or standard_deviation is numerically invalid.
        1 if the difference is outside the specified range,
        0 otherwise.
    """
    if (
        not isvalid(value)
        or not isvalid(climate_normal)
        or not isvalid(maximum_anomaly)
        or not isvalid(standard_deviation)
    ):
        return untestable

    if maximum_anomaly <= 0:
        return untestable

    if standard_deviation_limits is not None:
        if standard_deviation_limits[1] <= standard_deviation_limits[0]:
            return untestable

        if standard_deviation < standard_deviation_limits[0]:
            standard_deviation = standard_deviation_limits[0]
        if standard_deviation > standard_deviation_limits[1]:
            standard_deviation = standard_deviation_limits[1]

    climate_diff = abs(value - climate_normal)

    if lowbar is None:
        low_check = True
    else:
        low_check = climate_diff > lowbar

    if climate_diff / standard_deviation > maximum_anomaly and low_check:
        return failed

    return passed


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


def hard_limit_check(val: float, limits: tuple[float, float]) -> int:
    """Check if a value is outside specified limits.

    Parameters
    ----------
    val: float
        Value to be tested.
    limits: tuple of float
        A tuple of two floats representing the lower and upper limit.

    Returns
    -------
    int
        2 if limits[1] is equal or less than limits[0] of if val is numerically invalid or None,
        1 if val is outside the limits,
        0 otherwise
    """
    if limits[1] <= limits[0]:
        return untestable

    if not isvalid(val):
        return untestable

    if limits[0] <= val <= limits[1]:
        return passed

    return failed


def sst_freeze_check(
    insst: float,
    sst_uncertainty: float,
    freezing_point: float,
    n_sigma: float,
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
    insst : float
        input SST to be checked
    sst_uncertainty : float
        the uncertainty in the SST value, defaults to zero
    freezing_point : float
        the freezing point of the water
    n_sigma : float
        number of sigma to use in the check

    Returns
    -------
    int
        2 if either insst, sst_uncertainty, freezing_point or n_sigma is numerically invalid or None,
        1 if the insst is below freezing point by more than twice the uncertainty,
        0 otherwise

    Note
    ----
    In previous versions, some parameters had default values:

        * ``sst_uncertainty``: 0.0
        * ``freezing_point``: -1.80
        * ``n_sigma``: 2.0
    """
    if not isvalid(insst):
        return untestable
    if not isvalid(sst_uncertainty):
        return untestable
    if not isvalid(freezing_point):
        return untestable
    if not isvalid(n_sigma):
        return untestable

    # fail if SST below the freezing point by more than twice the uncertainty
    if insst < (freezing_point - n_sigma * sst_uncertainty):
        return failed

    return passed
