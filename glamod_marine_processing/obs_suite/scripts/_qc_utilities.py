"""QC Utility functions for level1e script."""

from __future__ import annotations

import copy
import logging
import operator
import os

import numpy as np
import pandas as pd
from _utilities import read_cdm_tables
from marine_qc import qc_grouped_reports, qc_individual_reports, qc_sequential_reports
from marine_qc.external_clim import Climatology
from marine_qc.multiple_row_checks import do_multiple_row_check

op_map = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
}


def update_dtypes(data_df, table):
    """Update dtypes in DataFrame."""
    if table == "header":
        data_df["platform_type"] = data_df["platform_type"].astype(int)
        data_df["latitude"] = data_df["latitude"].astype(float)
        data_df["longitude"] = data_df["longitude"].astype(float)
        data_df["report_timestamp"] = pd.to_datetime(
            data_df["report_timestamp"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce",
        )
        data_df["station_speed"] = data_df["station_speed"].astype(float)
        data_df["station_course"] = data_df["station_course"].astype(float)
        data_df["report_quality"] = data_df["report_quality"].astype(int)
        data_df["location_quality"] = data_df["location_quality"].astype(int)
        data_df["report_time_quality"] = data_df["report_time_quality"].astype(int)
    else:
        data_df["observation_value"] = data_df["observation_value"].astype(float)
        data_df["latitude"] = data_df["latitude"].astype(float)
        data_df["longitude"] = data_df["longitude"].astype(float)
        data_df["date_time"] = pd.to_datetime(
            data_df["date_time"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce",
        )
        data_df["quality_flag"] = data_df["quality_flag"].astype(int)
    return data_df


def get_qc_columns(data_dict):
    """Copy data dictionary, convert values and get quality flags."""
    quality_flags = {}
    report_quality = pd.Series()
    location_quality = pd.Series()
    report_time_quality = pd.Series()
    history = pd.Series()
    data_dict_qc = {}

    for table, df in data_dict.items():
        update_dtypes(df, table)

        data_dict_qc[table] = df.copy()

        if table == "header":
            report_quality = df["report_quality"].copy()
            location_quality = df["location_quality"].copy()
            report_time_quality = df["report_time_quality"].copy()
            history = df["history"].copy()
        else:
            quality_flags[table] = df["quality_flag"].copy()

    return (
        data_dict_qc,
        report_quality,
        location_quality,
        report_time_quality,
        quality_flags,
        history,
    )


def get_single_qc_flag(df):
    """Get single QC flag from DataFrame containing multiple QC flags."""
    mask_0 = (df == 0).any(axis=1)
    mask_1 = (df == 1).any(axis=1)
    mask_2 = (df == 2).any(axis=1)
    mask_3 = (df == 3).any(axis=1)

    conditions = [mask_1, mask_0, mask_3, mask_2]
    choices = [1, 0, 3, 2]
    result = np.select(conditions, choices, default=2)
    return pd.Series(result, index=df.index, name="QC_FLAG")


def compare_quality_checks(df, location_quality, report_time_quality):
    """Compare entries with location_quality and report_time_quality."""
    df[location_quality == 2] = 1
    df[report_time_quality == 4] = 1
    df[report_time_quality == 5] = 1


def update_filenames(d, ext_path):
    """Ad external file path to file names."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "file_name":
                d[k] = os.path.join(ext_path, v)
            elif isinstance(v, dict):
                update_filenames(v, ext_path)


def open_netcdffiles(d):
    """Open filenames as Climatology objects."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "inputs":
                if not isinstance(v, dict):
                    continue
                d[k] = Climatology.open_netcdf_file(**v)
            elif isinstance(v, dict):
                open_netcdffiles(v)


def do_qc_individual(
    data_dict_qc,
    report_quality,
    location_quality,
    report_time_quality,
    quality_flags,
    params,
    ext_path,
):
    """Individual QC."""

    def do_qc_individual_header():
        # 1 Individual checks
        logging.info("1. Do individual checks")

        # 1.1. Header
        logging.info("1.1. Do header checks")
        qc_dict_header = qc_dict.get("header", {})

        data = data_dict_qc["header"]

        # 1.1.1. Position check
        logging.info("1.1.1. Do positional checks")

        # Deselect already failed location_qualities
        data_pos = data[location_quality != 2]
        idx_pos = data_pos.index

        # Do position check
        qc_dict_pos = qc_dict_header.get("position_check", {})
        pos_qc = do_multiple_row_check(
            data=data_pos,
            qc_dict=qc_dict_pos,
            return_method=return_method,
        )
        pos_qc = get_single_qc_flag(pos_qc)
        pos_qc = pos_qc.replace({1: 2, 2: 3})
        location_quality.loc[idx_pos] = pos_qc

        # 1.1.2. Time check
        logging.info("1.1.2. Do time checks")

        # Deselect already failed report_time_qualities
        data_time = data[(report_time_quality != 4) & (report_time_quality != 5)]

        # Do time check
        qc_dict_tme = qc_dict_header.get("time_check", {})
        time_qc = do_multiple_row_check(
            data=data_time,
            qc_dict=qc_dict_tme,
            return_method=return_method,
        )
        time_qc = get_single_qc_flag(time_qc)
        time_qc = time_qc.replace({1: 5, 2: 4, 3: 4})
        invalid_indexes = time_qc[time_qc != 0].index
        report_time_quality.loc[invalid_indexes] = time_qc[invalid_indexes]

        # 1.1.3. Report quality
        logging.info("1.1.3. Set report quality")
        compare_quality_checks(report_quality, location_quality, report_time_quality)

    def do_qc_individual_observations():
        # 1.2. Observations
        logging.info("1.2. Do observations checks")

        # 1.2.1. Do observation check
        i = 1
        for obs_table in data_dict_qc.keys():
            if obs_table == "header":
                continue
            logging.info(f"1.2.{i}. Do {obs_table} check")
            data = data_dict_qc[obs_table]
            quality_flag = quality_flags[obs_table]

            # Deselect already failed quality_flags
            data = data.loc[quality_flag != 1]

            # Deselect already failed report_qualities
            data = data.loc[report_quality != 1]

            # Deselect missing values
            qc_dict_miss = qc_dict.get("observations", {}).get("missing_values")
            miss_qc = do_multiple_row_check(
                data=data,
                qc_dict=qc_dict_miss,
                return_method=return_method,
            )
            miss_qc = get_single_qc_flag(miss_qc)
            miss_indexes = miss_qc[miss_qc == 1].index
            quality_flag.loc[miss_indexes] = 3
            data = data.drop(index=miss_indexes)

            idx_qc = data.index

            preproc_dict = qc_dict.get("preprocessing", {}).get(obs_table, {})
            qc_dict_obs = qc_dict.get("observations", {}).get(obs_table, {})
            update_filenames(preproc_dict, ext_path)
            open_netcdffiles(preproc_dict)
            obs_qc = do_multiple_row_check(
                data=data,
                preproc_dict=preproc_dict,
                qc_dict=qc_dict_obs,
                return_method=return_method,
            )
            obs_qc = get_single_qc_flag(obs_qc)

            # Flag quality_flag
            quality_flag.loc[idx_qc] = obs_qc
            compare_quality_checks(quality_flag, location_quality, report_time_quality)

            i += 1

    def do_qc_individual_combined():
        # 1.2.2. Do combined observation check
        qc_dict_comb = qc_dict.get("observations", {}).get("combined", {})
        i = 1
        for qc_name in qc_dict_comb.keys():
            logging.info(f"1.2.{i}. Do combined {qc_name} check")
            func = getattr(qc_individual_reports, qc_dict_comb[qc_name]["func"])
            tables = qc_dict_comb[qc_name]["tables"]
            names = qc_dict_comb[qc_name]["names"]
            inputs = {}
            calculate = True
            for ivar, table in tables.items():
                if table not in data_dict_qc.keys():
                    calculate = False
                    break
                data = data_dict_qc[table]
                column = names[ivar]
                inputs[ivar] = data[column]
            if calculate is False:
                continue
            series_list = list(inputs.values())
            common_indexes = set(series_list[0].index).intersection(
                *(s.index for s in series_list[1:])
            )
            common_indexes = list(common_indexes)
            for ivar, series in inputs.items():
                inputs[ivar] = inputs[ivar].loc[common_indexes]
            qc_flag = func(**inputs)
            idx_failed = qc_flag[qc_flag.isin([1])].index
            for table in tables.values():
                quality_flags[table].loc[idx_failed] = qc_flag.loc[idx_failed]

            i += 1

    # Get QC settings for individual reports
    qc_dict = params.qc_settings.get("individual_reports")
    return_method = qc_dict["return_method"]

    # Do header QC
    do_qc_individual_header()

    # Do observations QC
    do_qc_individual_observations()

    # Do combined QC
    do_qc_individual_combined()

    # Return updated quality flags
    return report_quality, location_quality, report_time_quality, quality_flags


def do_qc_sequential(
    data_dict_qc,
    report_quality,
    location_quality,
    quality_flags,
    idx_gnrc,
    params,
):
    """Sequential QC."""

    def do_qc_sequential_header():
        # 2. Sequential checks
        logging.info("2. Do sequential checks")
        qc_dict = params.qc_settings.get("sequential_reports", {})

        # 2.1. Header
        logging.info("2.1. Do header checks")
        qc_dict_header = qc_dict.get("header", {})
        data = data_dict_qc["header"].copy()

        # Deselect rows containing generic ids
        data = data.drop(index=idx_gnrc)

        i = 1
        for qc_name in qc_dict_header.keys():
            logging.info(f"2.1.{i}. Do {qc_name} check.")
            # Deselect already failed report_qualities
            data = data[~report_quality.loc[data.index].isin([1])]

            qc_dict_check = qc_dict_header[qc_name]
            func = getattr(qc_sequential_reports, qc_dict_check["func"])
            names = qc_dict_check.get("names", {})
            kwargs = qc_dict_check.get("arguments", {})
            idx_list = []
            for ps_id, subset in data.groupby("primary_station_id"):
                inputs = {k: subset[v] for k, v in names.items()}
                track_qc = func(**inputs, **kwargs)
                idx_failed = track_qc.index[track_qc == 1]
                if not idx_failed.empty:
                    idx_list.extend(idx_failed)

            location_quality.loc[idx_list] = 2
            report_quality.loc[idx_list] = 1

            i += 1

    def do_qc_sequential_observations():
        # 2.2. Observations
        logging.info("2.2. Do observation checks")

        # 2.2.1. Do observation track check
        qc_dict = params.qc_settings.get("sequential_reports", {}).get(
            "observations", {}
        )
        i = 1
        for obs_table in data_dict_qc.keys():
            if obs_table == "header":
                continue

            logging.info(f"2.2.{i}. Do {obs_table} checks")
            quality_flag = quality_flags[obs_table]
            data = data_dict_qc[obs_table]

            # Deselect rows containing generic ids
            idx_gnrc_obs = idx_gnrc.intersection(quality_flag.index)
            data = data.drop(index=idx_gnrc_obs)

            j = 1
            for qc_name in qc_dict.keys():
                logging.info(f"2.2.{i}.{j}. Do {qc_name} check")
                # Do the sequential check
                qc_dict_check = qc_dict[qc_name]
                func = getattr(qc_sequential_reports, qc_dict_check["func"])
                names = qc_dict_check.get("names", {})
                kwargs = qc_dict_check.get("arguments", {})
                preproc = qc_dict_check.get("preproc", {})
                tables = qc_dict_check.get("tables", None)
                if isinstance(tables, list) and obs_table not in tables:
                    continue

                # Deselect already failed quality flags
                data = data[~quality_flag.loc[data.index] == 1]

                # Optionally, preprocess data
                data_cp = data.copy()
                if obs_table in preproc.keys():
                    col = preproc[obs_table]["column"]
                    op_str = preproc[obs_table]["operation"]
                    op_symbol, operand = op_str.strip().split()
                    operand = float(operand)
                    data_cp[col] = op_map[op_symbol](data_cp[col], operand)

                idx_list = []
                for ps_id, subset in data_dict_qc["header"].groupby(
                    "primary_station_id"
                ):
                    indexes = data_cp.index.intersection(subset.index)
                    subset_obs = data_cp.loc[indexes]
                    if subset_obs.empty:
                        continue
                    inputs = {k: subset_obs[v] for k, v in names.items()}
                    track_qc = func(**inputs, **kwargs)
                    idx_failed = track_qc.index[track_qc == 1]
                    if not idx_failed.empty:
                        idx_list.extend(idx_failed)

                quality_flag.loc[idx_list] = 1

                j += 1

            i += 1

    def do_qc_sequential_combined():
        # 2.2.2. Do combined observations track check
        qc_dict = params.qc_settings.get("sequential_reports", {}).get("combined", {})
        # !!!! Need updates
        return

        i = 1
        for qc_name in qc_dict.keys():
            logging.info(f"2.2.{i}. Do {qc_name} check")
            func = getattr(qc_sequential_reports, qc_dict[qc_name]["func"])
            tables = qc_dict[qc_name]["tables"]
            names = qc_dict[qc_name]["names"]
            kwargs = qc_dict[qc_name]["arguments"]

            inputs = {}
            for ivar, table in tables.items():
                data = data_dict_qc[table]
                column = names[ivar]
                inputs[ivar] = data[column]
            series_list = list(inputs.values())
            common_indexes = set(series_list[0].index).intersection(
                *(s.index for s in series_list[1:])
            )
            common_indexes = list(common_indexes)
            for ivar, series in inputs.items():
                inputs[ivar] = inputs[ivar].loc[common_indexes]
            qc_flag = func(**inputs, **kwargs)
            idx_failed = qc_flag[qc_flag.isin([1])].index
            for table in tables.values():
                quality_flags[table].loc[idx_failed] = qc_flag.loc[idx_failed]
            i += 1

    do_qc_sequential_header()

    do_qc_sequential_observations()

    do_qc_sequential_combined()

    return report_quality, location_quality, quality_flags


def do_qc_grouped(data_dict_qc, quality_flags, params, ext_path):
    """Grouped QC."""
    # 3. Buddy check
    logging.info("3. Do buddy checks")
    qc_dict = params.qc_settings.get("grouped_reports")

    # 3.1. Do observation buddy check
    preproc_dict = qc_dict.get("preprocessing", {})
    qc_dict_obs = qc_dict.get("observations")

    qc_dict_ind = params.qc_settings.get("individual_reports")
    preproc_dict_ind = qc_dict_ind.get("preprocessing", {})

    # Copy params for external buoy data
    params_buoy = copy.deepcopy(params)
    buoy_dataset = qc_dict.get("buoy_dataset", "None")
    buoy_dck = qc_dict.get("buoy_dck", "None")

    params_buoy.prev_level_path = params_buoy.prev_level_path.replace(
        params.dataset, buoy_dataset
    )
    params_buoy.prev_level_path = params_buoy.prev_level_path.replace(
        params.sid_dck, buoy_dck
    )

    i = 1
    for obs_table in data_dict_qc:
        if obs_table == "header":
            continue
        logging.info(f"3.{i}. Do {obs_table} checks")
        quality_flag = quality_flags[obs_table]
        data = data_dict_qc[obs_table]

        # Add buoy data
        db_buoy = pd.DataFrame()
        if buoy_dataset != "None" and buoy_dck != "None":
            db_buoy = read_cdm_tables(params_buoy, obs_table)
        if not db_buoy.empty:
            data_buoy = db_buoy[obs_table].set_index("report_id", drop=False)
            update_dtypes(data_buoy, obs_table)
            data_obs = pd.concat([data, data_buoy])
            indexes_buoy = data_buoy.index
            ignore_indexes = data_obs.index.get_indexer(indexes_buoy)
        else:
            logging.warning(
                f"Could not find any {obs_table} {buoy_dataset} data for {params_buoy.prev_fileID}: {params_buoy.prev_level_path}"
            )
            indexes_buoy = []
            ignore_indexes = None

        # Pre-processing
        preproc_dict_obs = preproc_dict.get(obs_table, {})
        preproc_dict_ind_obs = preproc_dict_ind.get(obs_table, {})

        for var_name in preproc_dict_obs.keys():
            if preproc_dict_obs[var_name] == "__individual_reports__":
                preproc_dict_obs[var_name] = preproc_dict_ind_obs.get(var_name, {}).get(
                    "inputs"
                )

        update_filenames(preproc_dict_obs, ext_path)
        open_netcdffiles(preproc_dict_obs)

        # Get table-specific arguments
        qc_dict_obs_sp = qc_dict.get(obs_table, {})

        for var_name in preproc_dict_obs.keys():
            if not isinstance(preproc_dict_obs[var_name], dict):
                continue
            if "inputs" in preproc_dict_obs[var_name].keys():
                preproc_dict_obs[var_name] = preproc_dict_obs[var_name]["inputs"]

        j = 1
        for qc_name in qc_dict_obs.keys():
            if obs_table not in qc_dict_obs[qc_name]["tables"]:
                continue
            logging.info(f"3.{i}.{j}. Do {qc_name} check")

            # Deselect already failed quality flags
            obs_indexes = data.index.difference(indexes_buoy)
            failed_indexes = quality_flag.loc[obs_indexes].isin([1]).index
            data = data.drop(failed_indexes)

            # Do the buddy check
            qc_dict_check = qc_dict_obs[qc_name]
            func = getattr(qc_grouped_reports, qc_dict_check["func"])
            names = qc_dict_check.get("names", {})
            inputs = {k: data[v] for k, v in names.items()}
            kwargs = qc_dict_check.get("arguments", {})
            for var_name, value in kwargs.items():
                if isinstance(value, str) and value == "__preprocessed__":
                    kwargs[var_name] = preproc_dict_obs[var_name]
            kwargs["ignore_indexes"] = ignore_indexes
            for arg_name, arg_value in qc_dict_obs_sp.get(qc_name, {}).items():
                kwargs[arg_name] = arg_value

            qc_flag = func(**inputs, **kwargs)
            idx_failed = qc_flag[qc_flag.isin([1])].index
            quality_flag.loc[idx_failed] = qc_flag.loc[idx_failed]

            j += 1

        i += 1

    return quality_flags


def do_qc(
    data_dict_qc,
    report_quality,
    location_quality,
    report_time_quality,
    quality_flags,
    history,
    history_add,
    params,
    ext_path,
):
    """QC."""
    # Set observation quality_flag on blacklist and deselect them
    idx_blck = report_quality[report_quality == 6].index
    for table in data_dict_qc.keys():
        if table == "header":
            data_dict_qc[table].drop(index=idx_blck, inplace=True)
            idx_not_blck = data_dict_qc[table].index
            history.loc[idx_not_blck] = history.loc[idx_not_blck].apply(
                lambda x: x + history_add
            )
            continue

        idx_blck_obs = idx_blck.intersection(quality_flags[table].index)
        quality_flags[table].loc[idx_blck_obs] = 6
        data_dict_qc[table].drop(index=idx_blck_obs, inplace=True)

    # Set indexes of generic ID reports
    idx_gnrc = report_quality[report_quality == 88].index

    # Do the quality control
    report_quality, location_quality, report_time_quality, quality_flags = (
        do_qc_individual(
            data_dict_qc=data_dict_qc,
            report_quality=report_quality,
            location_quality=location_quality,
            report_time_quality=report_time_quality,
            quality_flags=quality_flags,
            params=params,
            ext_path=ext_path,
        )
    )

    report_quality, location_quality, quality_flags = do_qc_sequential(
        data_dict_qc=data_dict_qc,
        report_quality=report_quality,
        location_quality=location_quality,
        quality_flags=quality_flags,
        idx_gnrc=idx_gnrc,
        params=params,
    )

    quality_flags = do_qc_grouped(
        data_dict_qc=data_dict_qc,
        quality_flags=quality_flags,
        params=params,
        ext_path=ext_path,
    )

    return report_quality, location_quality, report_time_quality, quality_flags, history
