from __future__ import annotations

import datetime
import re

import numpy as np
import pandas as pd
import pytest
from pint.errors import DimensionalityError

from glamod_marine_processing.qc_suite.modules.auxiliary import (
    convert_units,
    inspect_arrays,
    post_format_return_type,
)
from glamod_marine_processing.qc_suite.modules.external_clim import inspect_climatology
from glamod_marine_processing.qc_suite.modules.time_control import convert_date


@convert_units(value="K")
def _convert_function(value):
    return value


@inspect_arrays(["value1", "value2"])
def _array_function(value1, value2):
    return value1, value2


@inspect_arrays(["value1", "value3"])
def _array_function2(value1, value2):
    return value1, value2


@convert_date(["year", "month", "day"])
def _date_function(date, year=None, month=None, day=None):
    return year, month, day


@convert_date(["year2", "month", "day"])
def _date_function2(date, year=None, month=None, day=None):
    return year, month, day


@pytest.mark.parametrize("units", [{"value": "degC"}, "degC"])
def test_convert_units(units):
    result = _convert_function(30.0, units=units)
    assert result == 30.0 + 273.15


def test_convert_units_no_conversion():
    result = _convert_function(30.0, units={"value2": "degC"})
    assert result == 30.0


def test_convert_units_raise():
    with pytest.raises(DimensionalityError):
        _convert_function(30.0, units="hPa")


@pytest.mark.parametrize(
    "value1, value2",
    [
        [2, 3],
        [[5, 8, 9], [7, 2, 3]],
        [pd.Series([4, 6, 9]), [8, 6, 1]],
        [np.array([8, 9, 3]), pd.Series([9, 8, 3])],
        [np.array([8, 6, 9]), [8, 3, 7]],
    ],
)
def test_inspect_arrays(value1, value2):
    result1, result2 = _array_function(value1, value2)
    expected1 = np.atleast_1d(value1)
    expected2 = np.atleast_1d(value2)
    assert np.array_equal(result1, expected1)
    assert np.array_equal(result2, expected2)


def test_inspect_arrays_raise_dimension():
    with pytest.raises(ValueError, match="Input 'value1' must be one-dimensional."):
        _array_function(np.ndarray(shape=(2, 2), dtype=float, order="F"), [1, 2, 3])


def test_inspect_arrays_raise_length():
    error_msg = "Input ['value1', 'value2'] must all have the same length."
    escaped_msg = re.escape(error_msg)
    with pytest.raises(ValueError, match=escaped_msg):
        _array_function([1, 2, 3, 4], [1, 2, 3])


def test_inspect_arrays_raise_parameter():
    with pytest.raises(
        ValueError, match="Parameter 'value3' is not a valid parameter."
    ):
        _array_function2(1, 2)


@pytest.mark.parametrize(
    "date, year, month, day",
    [["2019-9-27", 2019, 9, 27], ["2019-9", 2019, 9, 1], ["2019", 2019, 1, 1]],
)
def test_convert_date(date, year, month, day):
    yy, mm, dd = _date_function(pd.to_datetime(date))
    assert yy == year
    assert mm == month
    assert dd == day


def test_convert_date_raise():
    with pytest.raises(ValueError, match="Parameter 'year2' is not a valid parameter."):
        _date_function2(pd.to_datetime("2019-09-27"))
