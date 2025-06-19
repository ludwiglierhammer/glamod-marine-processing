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


class TypeContext:
    """
    A container class to hold original (unmodified) function argument values.

    This class is useful for preserving the initial inputs before any
    processing or transformation steps are applied, enabling later access
    to the original user inputs.

    Attributes
    ----------
    originals : dict
        A dictionary mapping parameter names to their original values.
    """

    def __init__(self):
        self.originals = {}


def save_originals(args: dict, kwargs: dict) -> TypeContext:
    """
    Store original argument values in a TypeContext.

    This function checks if a `_ctx` (TypeContext) object is already present
    in either the keyword arguments or positional arguments. If not found,
    it creates a new TypeContext. It then records all argument names and
    values from `args` into the `originals` dictionary of the context, skipping
    those already stored.

    Parameters
    ----------
    args : dict
        Dictionary of function arguments (usually from `inspect.BoundArguments.arguments`).
    kwargs : dict
        Dictionary of keyword arguments passed to the function, used to check for existing `_ctx`.

    Returns
    -------
    TypeContext
        The context object containing the preserved original argument values.
    """
    ctx = kwargs.get("_ctx") or args.get("_ctx") or TypeContext()
    for param, value in args.items():
        if param not in ctx.originals:
            ctx.originals[param] = value
    return ctx


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


def isvalid(inval: ValueFloatType) -> bool | np.ndarray:
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
    Convert the result numpy array(s) to the same type as the input `value`.

    If result_array is a sequence of arrays, format each element recursively,
    preserving the container type.

    Parameters
    ----------
    result_array : np.ndarray
        The numpy array of results.
    input_values : scalar, sequence, np.ndarray, pd.Series or None
        One or more original input values to infer the desired return type from.

    Returns
    -------
    Same type as input(s)
        The result formatted to match the type of the first valid input value.
    """
    input_value = next((val for val in input_values if val is not None), None)

    if input_value is None or is_scalar_like(input_value):
        if hasattr(result_array, "ndim") and result_array.ndim > 0:
            result_array = result_array[0]
        return int(result_array)
    if isinstance(input_value, pd.Series):
        return pd.Series(result_array, index=input_value.index, dtype=int)
    if isinstance(input_value, (list, tuple)):
        return type(input_value)(result_array.tolist())
    return result_array  # np.ndarray or fallback


def post_format_return_type(params: list[str]) -> Callable:
    """
    Decorator to format a function's return value to match the type of its original input(s).

    This decorator ensures that the output of the decorated function is converted back
    to the same structure/type as the original input(s) specified by `params`.
    It uses a context object (`_ctx`) if available to retrieve the original inputs
    before any preprocessing was applied. If no context is found, it falls back to
    the current bound arguments.

    Parameters
    ----------
    params : list of str
        List of parameter names whose original input types should be used to
        format the return value.

    Returns
    -------
    Callable
        A decorator that modifies the decorated function's output to match the
        input types.

    Notes
    -----
    - Assumes a `TypeContext` object may be passed via `_ctx` keyword argument,
      storing original input values for accurate type formatting.
    - Falls back gracefully if no context is available, using current arguments.
    - Useful when function inputs are preprocessed (e.g., converted to arrays),
      and the output should match the original input types.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ctx = kwargs.pop("_ctx", None)
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Get original input values from context if available
            if ctx is not None:
                input_values = [ctx.originals.get(p) for p in params]
            else:
                # Fallback to current values
                input_values = [bound_args.arguments.get(p) for p in params]

            result = func(*bound_args.args, **bound_args.kwargs)
            return format_return_type(result, *input_values)

        return wrapper

    return decorator


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

            ctx = save_originals(bound_args.arguments, kwargs)
            arrays = []
            for param in params:
                if param not in bound_args.arguments:
                    raise ValueError(f"Parameter {param} is not a valid parameter.")

                value = bound_args.arguments[param]

                if value is None and skip_none:
                    continue

                arr = np.atleast_1d(value)
                if arr.ndim != 1:
                    raise ValueError(f"Input '{param}' must be one-dimensional.")

                if replace is True:
                    bound_args.arguments[param] = arr

                arrays.append(arr)

            lengths = [len(arr) for arr in arrays]
            if any(length != lengths[0] for length in lengths):
                raise ValueError(f"Input {params} must all have the same length.")

            bound_args.arguments["_ctx"] = ctx
            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    return decorator
