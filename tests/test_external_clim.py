from __future__ import annotations

import numpy as np
import pytest
from cdm_reader_mapper.common.getting_files import load_file

from glamod_marine_processing.qc_suite.modules.Climatology import (
    Climatology as Climatology_exp,
)
from glamod_marine_processing.qc_suite.modules.external_clim import Climatology


@pytest.fixture(scope="session")
def external_clim():
    kwargs = {
        "cache_dir": ".pytest_cache/external_clim",
        "within_drs": False,
    }
    clim_dict = {}
    clim_dict["AT"] = {
        "mean": load_file(
            "metoffice_qc/external_files/AT_pentad_climatology.nc",
            **kwargs,
        ),
    }
    return clim_dict


@pytest.fixture(scope="session")
def external_at(external_clim):
    return Climatology.open_netcdf_file(
        external_clim["AT"]["mean"],
        "at",
        time_axis="pentad_time",
    )


@pytest.fixture(scope="session")
def expected_at(external_clim):
    return Climatology_exp.from_filename(
        external_clim["AT"]["mean"],
        "at",
    )


@pytest.mark.parametrize(
    "lat, lon, month, day",
    [
        [53.5, 10.0, 7, 4],
        [42.5, 1.4, 2, 16],
        [57.5, 9.4, 6, 1],
        [-68.4, -52.3, 11, 21],
        [-190.0, 10.0, 7, 4],
        [42.5, 95.0, 2, 16],
        [57.5, 9.4, 13, 1],
        [-68.4, -52.3, 11, 42],
        [None, 10.0, 7, 4],
        [42.5, None, 2, 16],
        [57.5, 9.4, None, 1],
        [-68.4, -52.3, 11, None],
    ],
)
def test_get_value(external_at, expected_at, lat, lon, month, day):
    kwargs = {
        "lat": lat,
        "lon": lon,
        "month": month,
        "day": day,
    }
    result = external_at.get_value(**kwargs)
    expected = expected_at.get_value(**kwargs)
    expected = np.float64(np.nan if expected is None else expected)
    assert np.allclose(result, expected, equal_nan=True)
