"""Spyder Editor.

This is a temporary script file.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import re
import sys

from glamod_marine_processing.utilities import mkdir

DATE_REGEX = r"([1-2]{1}[0-9]{3}\-(0[1-9]{1}|1[0-2]{1}))"


# FUNCTIONS -------------------------------------------------------------------
def config_element(
    sid_dck_log_dir,
    ai,
    script_config,
    sid_dck,
    yyyy,
    mm,
    filename=None,
):
    """Update configuration script."""
    script_config.update({"sid_dck": sid_dck})
    script_config.update({"yyyy": yyyy})
    script_config.update({"mm": mm})
    if filename is not None:
        script_config.update({"filename": filename})
    ai_config_file = os.path.join(sid_dck_log_dir, str(ai) + ".input")
    with open(ai_config_file, "w") as fO:
        json.dump(script_config, fO, indent=4)


def get_yyyymm(filename):
    """Extract date from filename."""
    yyyy_mm = re.search(DATE_REGEX, os.path.basename(filename))
    if not (yyyy_mm):
        logging.error(f"Could not extract date from filename {filename}")
        sys.exit(1)
    return yyyy_mm.group().split("-")


def clean_ok_logs(
    ai,
    ok_files,
    source_files,
    sid_dck,
    sid_dck_log_dir,
    job_file,
    source_dir,
    source_pattern,
    year_init,
    year_end,
    config,
):
    """Clean previous ok logs."""
    # Clean previous ok logs
    if len(ok_files) > 0:
        logging.info(f"Removing previous {len(ok_files)} logs")
        for x in ok_files:
            os.remove(x)
    for source_file in source_files:
        yyyy, mm = get_yyyymm(source_file)
        print(yyyy, mm)#exit()
        if int(yyyy) >= year_init and int(yyyy) <= year_end:
            config_element(sid_dck_log_dir, ai, config, sid_dck, yyyy, mm, source_file)
            ai += 1
        elif (int(yyyy) == year_init - 1 and int(mm) == 12) or (
            int(yyyy) == year_end + 1 and int(mm) == 1
        ):
            # include one month before and one after period to allow for qc within period
            config_element(sid_dck_log_dir, ai, config, sid_dck, yyyy, mm, source_file)
            ai += 1

    logging.info(f"{str(ai)} elements configured")
    if len(job_file) > 0:
        logging.info(f"Removing previous job file {job_file[0]}")
        os.remove(job_file[0])
    return ai


def clean_failed_logs_only(
    ai,
    failed_files,
    sid_dck,
    sid_dck_log_dir,
    job_file,
    source_dir,
    source_pattern,
    year_init,
    year_end,
    config,
):
    """Clean previous filed only logs."""
    logging.info(f"{sid_dck}: found {str(len(failed_files))} failed jobs")
    if len(job_file) > 0:
        logging.info(f"Removing previous job file {job_file[0]}")
        os.remove(job_file[0])
    for failed_file in failed_files:
        yyyy, mm = get_yyyymm(failed_file)
        source_file = re.sub("[?]{4}", yyyy, source_pattern)
        source_file = re.sub("[?]{2}", mm, source_file)
        source_file = os.path.join(source_dir, sid_dck, source_file)
        if int(yyyy) >= year_init and int(yyyy) <= year_end:
            config_element(sid_dck_log_dir, ai, config, sid_dck, yyyy, mm, source_file)
            ai += 1
        elif (int(yyyy) == year_init - 1 and int(mm) == 12) or (
            int(yyyy) == year_end + 1 and int(mm) == 1
        ):
            # include one month before and one after period to allow for qc within period
            config_element(sid_dck_log_dir, ai, config, sid_dck, yyyy, mm, source_file)
            ai += 1
    return ai


def clean_previous_ok_logs(
    log_dir,
    source_dir,
    source_pattern,
    sid_dck,
    script_config,
    release_periods,
    failed_only,
):
    """Make sure there are no previous input files."""

    def get_year(periods, sid_dck, yr_str):
        if sid_dck in periods.keys():
            return periods[sid_dck].get(yr_str)
        return periods.get(yr_str)

    # logging.info('Configuring data partition: {}'.format(sid_dck))
    sid_dck_log_dir = os.path.join(log_dir, sid_dck)
    mkdir(sid_dck_log_dir)
    job_file = glob.glob(os.path.join(sid_dck_log_dir, sid_dck + ".slurm"))

    # check is seperate configuration for this source / deck
    config = script_config.get(sid_dck)
    if config is None:
        config = script_config

    if not os.path.isdir(sid_dck_log_dir):
        logging.error(f"Data partition log directory does not exist: {sid_dck_log_dir}")
        sys.exit(1)

    year_init = get_year(release_periods, sid_dck, "year_init")
    year_end = get_year(release_periods, sid_dck, "year_end")
    # Make sure there are not previous input files
    ai = 1
    i_files = glob.glob(os.path.join(sid_dck_log_dir, "*.input"))
    if len(i_files) > 0:
        logging.info(f"Removing previous {len(i_files)} input files")
        for i_file in i_files:
            os.remove(i_file)

    ok_files = glob.glob(os.path.join(sid_dck_log_dir, "*.ok"))
    failed_files = glob.glob(os.path.join(sid_dck_log_dir, "*.failed"))
    logging.info(f"{os.path.join(source_dir, sid_dck, source_pattern)}")
    source_files = glob.glob(os.path.join(source_dir, sid_dck, source_pattern))
    logging.info(source_files)
    logging.info(
        f"Source dir: {source_dir}; sid_dck: {sid_dck}; Pattern: {source_pattern}"
    )

    if failed_only:
        if len(failed_files) > 0:
            ai = clean_failed_logs_only(
                ai,
                failed_files,
                sid_dck,
                sid_dck_log_dir,
                job_file,
                source_dir,
                source_pattern,
                year_init,
                year_end,
                config,
            )
        else:
            logging.info(f"{sid_dck}: no failed files")
    else:
        ai = clean_ok_logs(
            ai,
            ok_files,
            source_files,
            sid_dck,
            sid_dck_log_dir,
            job_file,
            source_dir,
            source_pattern,
            year_init,
            year_end,
            config,
        )
    if len(failed_files) > 0:
        logging.info(f"Removing previous {len(failed_files)} failed logs")
        for x in failed_files:
            os.remove(x)


# %% -----------------------------------------------------------------------------


def main(
    source_dir,
    source_pattern,
    log_dir,
    script_config,
    release_periods,
    process_list,
    failed_only=False,
):
    """Configuration main function."""
    logging.basicConfig(
        format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
        level=logging.INFO,
        datefmt="%Y%m%d %H:%M:%S",
        filename=None,
    )
    if failed_only:
        logging.info("Configuration using failed only mode")
    # %%
    for sid_dck in process_list:
        clean_previous_ok_logs(
            log_dir,
            source_dir,
            source_pattern,
            sid_dck,
            script_config,
            release_periods,
            failed_only,
        )

    return 0


if __name__ == "__main__":
    main()
