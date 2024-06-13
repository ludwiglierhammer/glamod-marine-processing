from __future__ import annotations

from _settings import level_input, prev_level, table_names
from cdm_reader_mapper.common.getting_files import load_file


def load_NOC_corrections(**kwargs):
    """Load NOC correction data from cdm-testdata."""
    for sub in [
        "duplicate_flags",
        "duplicates",
        "id",
        "latitude",
        "longitude",
        "timestamp",
    ]:
        load_file(
            f"NOC_corrections/v1x2023/{sub}/2022-01.txt.gz",
            **kwargs,
        )


def load_NOC_ANC_INFO(**kwargs):
    """Load NOC ANC INFO data from cdm-testdata."""
    load_file(
        "NOC_ANC_INFO/json_files/dck992.json",
        **kwargs,
    )


def load_Pub47(**kwargs):
    """Load Pub47 data from cdm-testdata."""
    load_file(
        "Pub47/monthly/2022-01-01.csv",
        **kwargs,
    )


def load_metoffice_qc(**kwargs):
    """Load metoffice QC data from cdm-testdata."""
    for qc_file in [
        "AT_qc_202201_CCIrun.csv",
        "DPT_qc_202201_CCIrun.csv",
        "POS_qc_202201_CCIrun.csv",
        "SLP_qc_202201_CCIrun.csv",
        "SST_qc_202201_CCIrun.csv",
        "SST_qc_202201_hires_CCIrun.csv",
        "Variables_202201_CCIrun.csv",
        "W_qc_202201_CCIrun.csv",
    ]:
        load_file(f"metoffice_qc/base/2022/01/{qc_file}", **kwargs)


def load_input(level):
    """Load level input data data from cdm-testdata."""
    p_level = prev_level[level]
    leveli = level_input[level]
    if level == "level1a":
        load_imma(level, leveli, p_level)
    else:
        load_cdms(level, leveli, p_level)


def load_cdms(level, leveli, p_level):
    """Load level CDM input data from cdm-testdata."""
    for table_name in table_names:
        load_file(
            f"imma1_992/cdm_tables/{table_name}-114-992_2022-01-01_subset.psv",
            cache_dir=f"./T{level}/{leveli}/ICOADS_R3.0.2T/{p_level}/114-992",
            within_drs=False,
        )


def load_imma(level, leveli, p_level):
    """Load level IMMA input data from cdm-testdata."""
    load_file(
        "imma1_992/input/114-992_2022-01-01_subset.imma",
        cache_dir=f"./T{level}/{leveli}/ICOADS_R3.0.2T/{p_level}/114-992",
        within_drs=False,
    )
