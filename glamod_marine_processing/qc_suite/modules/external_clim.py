"""Module to read external climatology files."""

from __future__ import annotations

import xarray as xr


class Climatology:
    """Class for dealing with climatologies, reading, extracting values etc.
    Automatically detects if this is a single field, pentad or daily climatology
    """

    def __init__(self, filename):
        self.filename = filename

    @classmethod
    def open_netcdf_file(cls, var_name, file_name):
        """Open filename with xarray."""
        ds = xr.open_dataset(file_name)
        da = ds[var_name]
        return cls(da)

    def get_value(self, lat=None, lon=None, month=None, day=None):
        """Get value from selection."""
        da_ = self.da.copy()
        if month is not None:
            da_ = da_.groupby("time.month")[month]
        if day is not None:
            da_ = da_.groupby("time.day")[day]
        if lat is not None:
            da_ = da_.sel(lat=lat, method="nearest")
        if lon is not None:
            da_ = da_.sel(lon=lon, method="nearest")
        return da_.values[0]
