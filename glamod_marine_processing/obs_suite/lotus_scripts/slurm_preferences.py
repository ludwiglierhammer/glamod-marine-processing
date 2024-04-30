"""SLURM preferences."""

level_source = {
    "level1a": "level0",
    "level1b": "level1a",
    "level1c": "level1b",
    "level1d": "level1c",
    "level1e": "level1d",
}

source_pattern = {
    "level1a": "IMMA1_R3.0.?T*_????-??",
    "level1b": "header-????-??-*.psv",
    "level1c": "header-????-??-*.psv",
    "level1d": "header-????-??-*.psv",
    "level1e": "header-????-??-*.psv",
}

nodesi = {
    "level1d": 1,
}

TaskPNi = {
    "level1d": 20,
}

ti = {
    "level1d": "02:00:00"
}
