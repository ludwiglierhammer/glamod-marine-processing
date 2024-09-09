from __future__ import annotations

import numpy as np

input_dir = "c_raid"
deck = "1260810"
cdm = f"{deck}_20041220"
output = "craid"
suffix = "nc"
level0 = f"{input_dir}/input/{cdm}.{suffix}"
process_list = "1260810"

table_names = [
    "header",
    "observations-at",
    "observations-dpt",
    "observations-slp",
    "observations-sst",
    "observations-wbt",
    "observations-wd",
    "observations-ws",
]

table_names_next = [
    "header",
    "observations-slp",
    "observations-sst",
]

prev_level = {
    "level1a": "level0",
    "level1b": "level1a",
    "level1c": "level1b",
    "level1d": "level1c",
    "level1e": "level1d",
    "level2": "level1e",
}

level_input = {
    "level1a": "datasets",
    "level1b": "release_7.0",
    "level1c": "release_7.0",
    "level1d": "release_7.0",
    "level1e": "release_7.0",
    "level2": "release_7.0",
}

which_tables = {
    "level1a": table_names,
    "level1b": table_names_next,
    "level1c": table_names_next,
    "level1d": table_names_next,
    "level1e": table_names_next,
    "level2": table_names_next,
}

pattern = {
    "level1a": "???????_????????.nc",
    "level1b": "header-?????.psv",
    "level1c": "header-?????.psv",
    "level1d": "header-?????.psv",
    "level1e": "header-?????.psv",
    "level2": "header-?????.psv",
}

drops = {
    "level1a": [0, 5, 6, 7, 9],
    "level1c": [0, 3],
}
