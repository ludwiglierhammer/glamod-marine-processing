"""Auxiliary functions for QC."""

from __future__ import annotations

import inspect
from collections.abc import Callable
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


def generic_decorator(handler: Callable[[dict], None]) -> Callable:
    """
    Base decorator that handles argument binding and applies a custom handler.

    Parameters
    ----------
    handler : Callable[[dict], None]
        A function that receives bound_args.arguments and can mutate/validate them.

    Returns
    -------
    Callable
        A decorator.
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
    """Create a decorator to inspect input sequences and convert them to numpy arrays.

    Parameters
    ----------
    params: list of str
        List of parameter names to be inspected.

    Returns
    -------
    Callable
        The decorator function
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


def convert_units() -> Callable:
    """Create a decorator to automatically convert source units to target units.

    Parameters
    ----------
    params: str
        Parameter name to convert units.

    Returns
    -------
    Callable
        The decorator function
    """

    def handler(arguments: dict, **meta_kwargs):
        converter_dict = meta_kwargs.get("converter_dict")
        if converter_dict is None:
            return

        for param, convert_units in converter_dict.items():
            if param not in arguments:
                raise ValueError(
                    f"Parameter '{param}' not found in function arguments."
                )

            value = arguments[param]
            if value is None:
                continue

            source_units = convert_units[0]
            target_units = convert_units[1]

            quantity = value * units(source_units)
            converted = convert_units_to(quantity, target_units)

            arguments[param] = converted

    # handler._decorator_kwargs = {"target_units", "source_units"}
    handler._decorator_kwargs = {"converter_dict"}

    return generic_decorator(handler)
