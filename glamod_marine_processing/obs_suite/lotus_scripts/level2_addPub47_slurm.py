#!/usr/bin/env python3
"""
Created on Wed Jul 22 09:09:41 2020

@author: iregou
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import subprocess
import sys

import config_array
import lotus_paths

# adaptation of level1d_slurm.py to add Pub47 metadata to level2 data for releases where it has initially been missed (avoiding to repeat a.o. the qc)


# Set process params-----------------------------------------------------------
LEVEL = "level2_update"
LEVEL_SOURCE = "level2"
SOURCE_PATTERN = "header-????-??-*.psv"
PYSCRIPT = "level2_addPub47.py"
USER = "glamod"
TaskPN = 20
NODES = 1
ti = "02:00:00"

exlude_sucessful = False
# use with care, e.g. if walltime was too short, but everything else is unchanged

# ------------------------------------------------------------------------------


def check_file_exit(files):
    """Check whether file exists."""
    files = [files] if not isinstance(files, list) else files
    for filei in files:
        if not os.path.isfile(filei):
            logging.error(f"File {filei} does not exist. Exiting")
            sys.exit(1)
    return


def check_dir_exit(dirs):
    """Check whether directory exists."""
    dirs = [dirs] if not isinstance(dirs, list) else dirs
    for diri in dirs:
        if not os.path.isdir(diri):
            logging.error(f"Directory {diri} does not exist. Exiting")
            sys.exit(1)
    return


def launch_process(process):
    """Launch process."""
    proc = subprocess.Popen(
        [process], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    jid_by, err = proc.communicate()
    if len(err) > 0:
        logging.error("Error launching process. Exiting")
        logging.info(f"Error is: {err}")
        sys.exit(1)
    jid = jid_by.decode("UTF-8").rstrip()

    return jid.split(" ")[-1]


# ------------------------------------------------------------------------------


logging.basicConfig(
    format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
    level=logging.INFO,
    datefmt="%Y%m%d %H:%M:%S",
    filename=None,
)

# Get process coordinates and build paths -------------------------------------
script_config_file = sys.argv[1]

check_file_exit([script_config_file])
with open(script_config_file) as fO:
    script_config = json.load(fO)


release = script_config["release"]
update = script_config["update"]
dataset = script_config["dataset"]
process_list_file = script_config["process_list_file"]
release_periods_file = script_config["release_periods_file"]
level_dir = script_config["level_dir"]  # os.path.join(data_dir,release,dataset,LEVEL)
level_source_dir = script_config[
    "level_source_dir"
]  # os.path.join(data_dir,release,dataset,LEVEL_SOURCE)
meta_dir = script_config["meta_dir"]


parser = argparse.ArgumentParser()
parser.add_argument("positional", metavar="N", type=str, nargs="+")
parser.add_argument("--failed_only")
parser.add_argument("--remove_source")

args = parser.parse_args()
if args.failed_only:
    logging.warning("failed_only is currently deactivated, all data will be processed")
    failed_only = True if args.failed_only == "yes" else False
else:
    failed_only = False
if args.remove_source:
    logging.warning(
        "remove_source has been discontinued, source data will not be removed"
    )
    remove_source = True if args.remove_source == "yes" else False
else:
    remove_source = False

# Get lotus paths
lotus_dir = lotus_paths.lotus_scripts_directory
scripts_dir = lotus_paths.scripts_directory
data_dir = lotus_paths.data_directory
scratch_dir = lotus_paths.scratch_directory

# Build process specific paths
release_tag = "-".join([release, update])
# script_config_file = os.path.join(config_path,release_tag,dataset,CONFIG_FILE)
# release_periods_file = os.path.join(config_path,release_tag,dataset,PERIODS_FILE)
# level_dir = os.path.join(data_dir,release,dataset,LEVEL)
# level_source_dir = os.path.join(data_dir,release,dataset,LEVEL_SOURCE)

log_dir = os.path.join(level_dir, "log")
# I think this is otherwise in source dir, but we have no permission here

# Check paths
check_file_exit([script_config_file, release_periods_file, process_list_file])
check_dir_exit([level_dir, level_source_dir, log_dir])

# Get configuration -----------------------------------------------------------

with open(process_list_file) as fO:
    process_list = fO.read().splitlines()

with open(release_periods_file) as fO:
    release_periods = json.load(fO)

# Build array input files -----------------------------------------------------
logging.info("CONFIGURING JOB ARRAYS...")

if not exlude_sucessful:
    status = config_array.main(
        level_source_dir,
        SOURCE_PATTERN,
        log_dir,
        script_config,
        release_periods,
        process_list,
        failed_only=failed_only,
    )
    if status != 0:
        logging.error("Creating array inputs")
        sys.exit(1)

# Build jobs ------------------------------------------------------------------
py_path = os.path.join(scripts_dir, PYSCRIPT)
# py_clean_path = os.path.join(lotus_dir,PYCLEAN)
# bsh_remove_path = os.path.join(scripts_dir,BSH_REMOVE_FILES)
pycommand = f"python {py_path} {data_dir} {release} {update} {dataset}"

# Set default job params
mem = script_config["job_memo_mb"]
t_hh = script_config["job_time_hr"]
t_mm = script_config["job_time_min"]
t = ":".join([t_hh, t_mm, "00"])

logging.info("SUBMITTING ARRAYS...")

job_file = os.path.join(log_dir, "sid_combined.slurm")
taskfarm_file = os.path.join(log_dir, "sid_combined.tasks")

if os.path.exists(taskfarm_file):
    logging.info("Removing previous tasks file")
    os.remove(taskfarm_file)

if 1:
    for sid_dck in process_list:
        log_diri = os.path.join(log_dir, sid_dck)
        log_token = False
        array_size = len(glob.glob(os.path.join(log_diri, "*.input")))
        if array_size == 0:
            logging.warning(f"{sid_dck}: no jobs for partition")
            continue

        memi = script_config.get(sid_dck, {}).get("job_memo_mb")
        memi = mem if not memi else memi
        TaskPNi = min(int(190000.0 / float(memi)), TaskPN)

        with open(taskfarm_file, "a") as fh:
            for i in range(array_size):
                if os.path.isfile(f"{log_diri}/{i+1}.failure"):
                    os.remove(f"{log_diri}/{i+1}.failure")
                if exlude_sucessful and os.path.isfile(f"{log_diri}/{i+1}.success"):
                    if not log_token:
                        logging.info(
                            f".success files exists in {log_diri}, those are not rerun!"
                        )
                        log_token = True
                else:
                    fh.writelines(
                        "{0} {1}/{2}.input > {1}/{2}.out 2> {1}/{2}.out; if [ $? -eq 0 ]; "
                        "then touch {1}/{2}.success; else touch {1}/{2}.failure; fi \n".format(
                            pycommand, log_diri, i + 1
                        )
                    )

with open(job_file, "w") as fh:
    fh.writelines("#!/bin/bash\n")
    fh.writelines("#SBATCH --job-name={}.job\n".format("addPub47"))
    fh.writelines(f"#SBATCH --nodes={NODES}\n")
    fh.writelines(f"#SBATCH -A {USER}\n")
    fh.writelines(f"#SBATCH --output={log_dir}/%j.out\n")
    fh.writelines(f"#SBATCH --error={log_dir}/%j.err\n")
    fh.writelines(f"#SBATCH --time={ti}\n")
    # fh.writelines('#SBATCH --mem={}\n'.format(memi))
    fh.writelines("#SBATCH --open-mode=truncate\n")
    fh.writelines("module load taskfarm\n")
    # fh.writelines('TMPDIR=/ichec/home/users/awerneck/scratch/local\n')
    # fh.writelines('export TMPDIR\n')
    # fh.writelines('cd "$TMPDIR"\n')
    # fh.writelines('cp {} .\n'.format(level_source_dir))
    # fh.writelines('cp {} .\n'.format(meta_dir))
    # fh.writelines('mkdir out\n')
    # fh.writelines('cd out\n')
    # fh.writelines('find {} -type d > dirs.txt\n')
    # fh.writelines('xargs mkdir -p < dirs.txt\n')
    # fh.writelines('cd ..\n')
    fh.writelines(f"export TASKFARM_PPN={TaskPN}\n")
    # fh.writelines('export TASKFARM_GROUP=20\n')
    fh.writelines(f"taskfarm {taskfarm_file}\n")

logging.info(f"launching {job_file}")
process = f"jid=$(sbatch {job_file} | cut -f 4 -d' ') && echo $jid"
jid = launch_process(process)
