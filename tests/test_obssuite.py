from __future__ import annotations

import pytest
from _testing_suite import _obs_testing


@pytest.mark_parametrize(
    "dataset", ["C-RAID_1.2", "ICOADS_R3.0.2T"]
)
@pytest.mark.parametrize(
    "level", ["level1a", "level1b", "level1c", "level1d", "level1e", "level2"]
)
def test_levels(capsys, dataset, level):
    _obs_testing(level, capsys)
