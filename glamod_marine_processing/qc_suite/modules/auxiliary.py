"""Auxiliary functions for QC."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from functools import wraps

import numpy as np
import pandas as pd

passed = 0
failed = 1
untestable = 2
untested = 3


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

                arr = np.asarray(bound_args.arguments[name])
                if arr.ndim != 1:
                    raise ValueError(f"Input '{name}' must be one-dimensional.")
                arrays.append(arr)

                bound_args.arguments[name] = arr
            lengths = [len(arr) for arr in arrays]
            if any(length != lengths[0] for length in lengths):
                raise ValueError(f"Input {params} must all have the same length.")

            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper

    return decorator
