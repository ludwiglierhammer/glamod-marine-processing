"""Module containing QC functions for deck level QC checks which could be applied on a DataBundle."""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

import glamod_marine_processing.qc_suite.modules.time_control as time_control

from glamod_marine_processing.qc_suite.modules.qc import failed, passed

km_to_nm = 0.539957


