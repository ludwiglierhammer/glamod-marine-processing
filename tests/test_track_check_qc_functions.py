import pytest
import pandas as pd

from glamod_marine_processing.qc_suite.modules.next_level_track_check_qc import spike_check


@pytest.fixture
def test_frame():

    pt = [1 for _ in range(30)]
    lat = [-5. + i * 0.1 for i in range(30)]
    lon = [0 for _ in range(30)]
    sst = [22 for _ in range(30)]
    sst[15] = 33

    date = pd.date_range(start=f'1850-01-01', freq='1h', periods=len(pt))

    df = pd.DataFrame(
        {
            'sst': sst,
            'date': date,
            'lat': lat,
            'lon': lon,
            'pt': pt
        }
    )

    return df


def test_spike_check(test_frame):
    result = spike_check(test_frame)
    for i in range(30):
        row = result.iloc[i]
        if i == 15:
            assert row.spike == 1
        else:
            assert row.spike == 0

@pytest.mark.parametrize(
    "key",
    ['sst', 'lat', 'lon', 'pt', 'date']
)
def test_spike_check_raises(test_frame, key):
    test_frame.drop(labels=[key], axis=1, inplace=True)
    with pytest.raises(KeyError):
        spike_check(test_frame)