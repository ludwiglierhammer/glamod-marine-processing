"""Quality control NOC auxiliary module."""

from __future__ import annotations

import pandas as pd

imiss = -99999
fmiss = pd.np.nan
cmiss = "__EMPTY"
tmiss = pd.NaT


def to_none(value):
    """Return missing values as None."""
    if (value == imiss) | (value == fmiss) | (value == cmiss) | (value == tmiss):
        return None
    else:
        return value
