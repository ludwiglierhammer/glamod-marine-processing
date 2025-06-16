"""Auxiliary functions for QC."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from functools import wraps

import numpy as np
import pandas as pd
from xclim.core.units import convert_units_to, units

passed = 0
failed = 1
untestable = 2
untested = 3


def isvalid(inval: float | None) -> bool:
    """Check if a value is numerically valid.

    Parameters
    ----------
    inval : float or None
        The input value to be tested

    Returns
    -------
    booll
        Returns False if the input value is numerically invalid or None, True otherwise
    """
    if pd.isna(inval):
        return False
    return True


# def get_target_units(target_units):


def convert_to(
    value: float | None | Sequence[float | None], source_units: str, target_units: str
):
    """Convert a float with source units into target units.

    Parameters
    ----------
    value: float or None or array-like of float or None
        A single float value, None, or a sequence (e.g., list, tuple, array-like)
        containing floats and/or None values. `None` values will be ignored or passed
        through unchanged.
    source_units: str
        The units of the input value(s) (e.g., 'degC', 'm/s').
    target_units: str
        The units to convert to (e.g., 'K', 'km/h').

    Returns
    -------
    float or None or array-like of float or None
        Converted value(s) with the same structure as input,
        where floats are converted and None values are preserved.
    """

    def _convert_to(value):
        if not isvalid(value):
            return value
        return convert_units_to(value * registry, target_units)

    registry = units(source_units)
    if target_units == "unknown":
        target_units = registry.to_base_units()

    if isinstance(value, np.ndarray):
        return np.array([_convert_to(v) for v in value])
    if isinstance(value, Sequence):
        return type(value)(_convert_to(v) for v in value)
    return _convert_to(value)


def generic_decorator(handler: Callable[[dict], None]) -> Callable:
    """
    Creates a decorator that binds function arguments, allows inspection or modification
    of those arguments via a custom handler function, and then calls the original function.

    This base decorator manages argument binding and supports passing additional reserved
    keyword arguments to the handler through the decorated function's kwargs.

    Parameters
    ----------
    handler : Callable[[dict], None]
        A function that takes a dictionary of bound arguments (`bound_args.arguments`)
        and optionally other keyword arguments, to inspect, mutate, or validate these
        arguments before the decorated function executes.
        The handler should accept the signature:
        `handler(arguments: dict, **meta_kwargs) -> None`

    Returns
    -------
    Callable
        A decorator that can be applied to any function. The decorated function will
        have its arguments bound and passed to the handler before execution.

    Notes
    -----
    - The handler can specify a `_decorator_kwargs` attribute (a set of reserved keyword
      argument names). These reserved kwargs will be extracted from the decorated function's
      call kwargs and passed to the handler, then removed before calling the original function.
    - The original function is called with the possibly modified bound arguments after
      handler processing.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            reserved_keys = getattr(handler, "_decorator_kwargs", set())
            meta_kwargs = {k: kwargs.pop(k) for k in reserved_keys if k in kwargs}

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            handler.__funcname__ = func.__name__
            handler(
                bound_args.arguments, **meta_kwargs
            )  # Perform specific inspection/modification

            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    return decorator


def inspect_arrays(params: list[str]) -> Callable:
    """
    Create a decorator that inspects specified input parameters of a function,
    converts them to one-dimensional NumPy arrays, and validates their lengths.

    This decorator is useful to enforce that certain input arguments are sequence-like,
    convert them to NumPy arrays for consistent processing, and ensure they all have
    the same length.

    Parameters
    ----------
    params : list of str
        A list of parameter names to inspect in the decorated function's arguments.
        Each named parameter will be converted to a NumPy array and validated.

    Returns
    -------
    Callable
        A decorator function that can be applied to other functions. When applied,
        the specified parameters will be converted to 1D NumPy arrays, validated
        to ensure they exist and have matching lengths, and then passed to the
        decorated function.

    Raises
    ------
    ValueError
        If any specified parameter name is not found in the decorated function's
        arguments.
        If any of the specified parameters is not one-dimensional.
        If the lengths of the specified arrays do not all match.

    Examples
    --------
    >>> @inspect_arrays(["a", "b"])
    ... def add_arrays(a, b):
    ...     return a + b
    ...

    >>> add_arrays([1, 2, 3], [4, 5, 6])
    array([5, 7, 9])

    >>> add_arrays([1, 2], [3, 4, 5])
    Traceback (most recent call last):
        ...
    ValueError: Input ['a', 'b'] must all have the same length.
    """

    def handler(arguments: dict, **meta_kwargs):
        arrays = []
        for name in params:
            if name not in arguments:
                raise ValueError(f"Parameter {name} is not a valid parameter.")

            arr = np.asarray(arguments[name])
            if arr.ndim != 1:
                raise ValueError(f"Input '{name}' must be one-dimensional.")
            arrays.append(arr)

            arguments[name] = arr
        lengths = [len(arr) for arr in arrays]
        if any(length != lengths[0] for length in lengths):
            raise ValueError(f"Input {params} must all have the same length.")

    return generic_decorator(handler)


def convert_units(**units_by_name) -> Callable:
    """
    Create a decorator to automatically convert units of specified function parameters.

    This decorator uses a `converter_dict` keyword argument to specify which parameters
    should be converted, along with their source and target units. Before the decorated
    function runs, the specified parameters are converted using the `convert_to` function.

    Parameters
    ----------
    None

    Returns
    -------
    Callable
        A decorator function that, when applied to another function, automatically
        converts the units of specified parameters according to the provided
        `converter_dict`.

    Notes
    -----
    - The decorator expects the decorated function to be called with a keyword argument
      `converter_dict`, which is a dictionary mapping parameter names (str) to tuples
      of `(source_units: str, target_units: str)`.
    - Parameters not present in the function arguments or with a value of None are
      skipped.
    - Uses the `convert_to` function to perform the actual unit conversion.

    Examples
    --------
    >>> @convert_units()
    ... def temperature_in_K(temp):
    ...     print(f"Temperature in Kelvin: {temp}")
    ...

    >>> temperature_in_K(25.0, converter_dict={"temp": ("degC", "K")})
    Temperature in Kelvin: 298.15
    """

    def handler(arguments: dict, **meta_kwargs):
        units_dict = meta_kwargs.get("units")
        if units_dict is None:
            return

        for param, target_units in units_by_name.items():
            if param not in arguments:
                raise ValueError(
                    f"Parameter '{param}' not found in function arguments."
                )
            if param not in units_dict:
                continue

            value = arguments[param]
            if value is None:
                continue

            source_units = units_dict[param]

            converted = convert_to(value, source_units, target_units)

            arguments[param] = converted

    handler._decorator_kwargs = {"units"}

    return generic_decorator(handler)
