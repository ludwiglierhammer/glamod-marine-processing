from __future__ import annotations

from cdm_reader_mapper.common.getting_files import load_file


def load_noc_anc_info(**kwargs):
    """Load NOC ANC INFO data from cdm-testdata."""
    load_file(
        "NOC_ANC_INFO/v2025/dck992.json",
        **kwargs,
    )


def load_pub47(**kwargs):
    """Load Pub47 data from cdm-testdata."""
    load_file(
        "Pub47/v202501/pub47_2022_01.csv",
        **kwargs,
    )


def load_input(dataset, level, settings, cache_dir):
    """Load level input data data from cdm-testdata."""
    p_level = settings.prev_level[level]
    leveli = settings.level_input[level]
    process_list = settings.process_list
    cache_dir = f"{cache_dir}/{leveli}/{dataset}/{p_level}/{process_list}"
    if level == "level1a":
        load_level0(cache_dir, settings)
    else:
        load_cdms(cache_dir, settings)
    return cache_dir


def load_cdms(cache_dir, settings):
    """Load level CDM input data from cdm-testdata."""
    for table_name in settings.table_names:
        load_file(
            f"{settings.input_dir}/cdm_tables/{table_name}-{settings.cdm}.psv",
            cache_dir=cache_dir,
            within_drs=False,
        )


def load_level0(cache_dir, settings):
    """Load level0 input data from cdm-testdata."""
    load_file(
        settings.level0,
        cache_dir=cache_dir,
        within_drs=False,
    )
