"""Auxiliary functions for QC."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from datetime import datetime
from functools import wraps
from typing import Any, TypeAlias

import numpy as np
import numpy.typing as npt
import pandas as pd

passed = 0
failed = 1
untestable = 2
untested = 3

PandasNAType: TypeAlias = type(pd.NA)
PandasNaTType: TypeAlias = type(pd.NaT)

# --- Scalars ---
ScalarIntType: TypeAlias = int | np.integer | PandasNAType | None
ScalarFloatType: TypeAlias = float | np.floating | PandasNAType | None
ScalarDatetimeType: TypeAlias = (
    datetime | np.datetime64 | pd.Timestamp | PandasNaTType | None
)

# --- Sequences ---
SequenceIntType: TypeAlias = (
    Sequence[ScalarIntType]
    | npt.NDArray[np.integer]
    | pd.Series  # optionally: pd.Series[np.integer] or pd.Series[pd.Int64Dtype]
)

SequenceFloatType: TypeAlias = (
    Sequence[ScalarFloatType]
    | npt.NDArray[np.floating]
    | pd.Series  # optionally: pd.Series[np.floating] or pd.Series[pd.Float64Dtype]
)

SequenceDatetimeType: TypeAlias = (
    Sequence[ScalarDatetimeType]
    | npt.NDArray[np.datetime64]
    | pd.Series  # optionally: pd.Series[pd.DatetimeTZDtype] or similar
)

# --- Value Types (Scalar or Sequence) ---
ValueFloatType: TypeAlias = ScalarFloatType | SequenceFloatType
ValueIntType: TypeAlias = ScalarIntType | SequenceIntType
ValueDatetimeType: TypeAlias = ScalarDatetimeType | SequenceDatetimeType


def is_scalar_like(x: Any) -> bool:
    """
    Return True if the input is scalar-like (i.e., has no dimensions).

    A scalar-like value includes:
    - Python scalars: int, float, bool, None
    - NumPy scalars: np.int32, np.float64, np.datetime64, etc.
    - Zero-dimensional NumPy arrays: np.array(5)
    - Pandas scalars: pd.Timestamp, pd.Timedelta, pd.NA, pd.NaT
    - Strings and bytes (unless excluded)

    Parameters
    ----------
        x (Any): The value to check.

    Returns
    -------
        bool: True if `x` is scalar-like, False otherwise.
    """
    try:
        return np.ndim(x) == 0
    except TypeError:
        return True  # fallback: built-in scalars like int, float, pd.Timestamp


def isvalid(
    inval: float | None | Sequence[float | None] | np.ndarray,
) -> bool | np.ndarray:
    """Check if a value(s) are numerically valid (not None or NaN).

    Parameters
    ----------
    inval : float, None, array-like of float or None
        Input value(s) to be tested

    Returns
    -------
    bool or np.ndarray of bool
        Returns False where the input is None or NaN, True otherwise.
        Returns a boolean scalar if input is scalar, else a boolean array.
    """
    result = np.logical_not(pd.isna(inval))
    if np.isscalar(inval):
        return bool(result)
    return result


def format_return_type(result_array: np.ndarray, *input_values: Any) -> Any:
    """
    Convert the result numpy array to the same type as the input `value`.

    Parameters
    ----------
    result_array : np.ndarray
        The numpy array of results.
    input_values : scalar, sequence, np.ndarray, pd.Series or None
        One or more original input values to infer the desired return type from.

    Returns
    -------
    Same type as input
        The result formatted to match the type of the first valid input value.

    Raises
    ------
    ValueError
        If all input_values are None, so the output type cannot be inferred.
    """
    input_value = next((val for val in input_values if val is not None), None)
    if input_value is None or is_scalar_like(input_value):
        return int(result_array)
    if isinstance(input_value, pd.Series):
        return pd.Series(result_array, index=input_value.index, dtype=int)
    if isinstance(input_value, (list, tuple)):
        return type(input_value)(result_array.tolist())
    return result_array  # np.ndarray or fallback


def inspect_arrays(params: list[str], replace=True, skip_none=False) -> Callable:
    """Create a decorator to inspect input sequences and convert them to numpy arrays.

    Parameters
    ----------
    params: list of str
        List of parameter names to be inspected.
    replace: bool, default: True
        Replace input parameters with inspected arrays.
    skip_none: bool, default: False
        Skip if param is None.

    Returns
    -------
    Callable
        The decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            arrays = []
            for name in params:
                if name not in bound_args.arguments:
                    raise ValueError(f"Parameter {name} is not a valid parameter.")

                if bound_args.arguments[name] is None and skip_none:
                    continue
                arr = np.atleast_1d(bound_args.arguments[name])
                if arr.ndim != 1:
                    raise ValueError(f"Input '{name}' must be one-dimensional.")

                if replace is True:
                    bound_args.arguments[name] = arr

                arrays.append(arr)

            lengths = [len(arr) for arr in arrays]
            if any(length != lengths[0] for length in lengths):
                raise ValueError(f"Input {params} must all have the same length.")

            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    return decorator
