from __future__ import annotations

import numpy as np
import pandas as pd

import glamod_marine_processing.qc_suite.modules.spherical_geometry as sg

def spike_check(df: pd.DataFrame) -> pd.DataFrame:
    """Perform IQUAM like spike check.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the data, must have columns 'sst', 'lat', 'lon', 'pt', 'date'

    Returns
    -------
    pd.DataFrame
        DataFrame as original but with 'spike' column added containing the spike check flags
    """
    for key in ['sst', 'lat', 'lon', 'pt', 'date']:
        if key not in df:
            raise KeyError(f'{key} not in dataframe')

    max_gradient_space = 0.5  # K/km
    max_gradient_time =  1.0 # K/hr

    ship_delta_t = 2.0  # K
    buoy_delta_t = 1.0  # K

    n_neighbours = 5

    numobs = len(df)

    if df.iloc[0].pt in [6,7]:
        delta_t = buoy_delta_t
    else:
        delta_t = ship_delta_t

    gradient_violations = []
    count_gradient_violations = []

    spike_qc = np.zeros(numobs)

    for t1 in range(numobs):

        violations_for_this_report = []
        count_violations_this_report = 0.0

        lo = max(0, t1 - n_neighbours)
        hi = min(numobs, t1 + n_neighbours + 1)

        for t2 in range(lo, hi):

            row1 = df.iloc[t1]
            row2 = df.iloc[t2]

            if row1.sst is not None and row2.sst is not None:

                distance = sg.sphere_distance(row1.lat, row1.lon, row2.lat, row2.lon)
                time_diff = abs((row2.date - row1.date).days * 24 + (row2.date - row1.date).seconds / 3600.)
                val_change = abs(row2.sst - row1.sst)

                iquam_condition = max(
                    [
                        delta_t,
                        abs(distance) * max_gradient_space,
                        abs(time_diff) * max_gradient_time,
                    ]
                )

                if val_change > iquam_condition:
                    violations_for_this_report.append(t2)
                    count_violations_this_report += 1.0

        gradient_violations.append(violations_for_this_report)
        count_gradient_violations.append(count_violations_this_report)

    count = 0
    while np.sum(count_gradient_violations) > 0.0:
        most_fails = np.argmax(count_gradient_violations)
        spike_qc[most_fails] = 1

        for index in gradient_violations[most_fails]:
            if most_fails in gradient_violations[index]:
                gradient_violations[index].remove(most_fails)
                count_gradient_violations[index] -= 1.0

        count_gradient_violations[most_fails] = 0
        count += 1

    df['spike'] = spike_qc

    return df