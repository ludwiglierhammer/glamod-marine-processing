from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import pytest
from _testing_suite import _obs_testing
from cdm_reader_mapper.cdm_mapper import read_tables
from cdm_reader_mapper.common.getting_files import load_file

from glamod_marine_processing.utilities import mkdir


@pytest.mark.parametrize(
    "level", ["level1a", "level1b", "level1c", "level1d", "level1e", "level2"]
)
def test_levels(capsys, level):
    _obs_testing(level, capsys)
