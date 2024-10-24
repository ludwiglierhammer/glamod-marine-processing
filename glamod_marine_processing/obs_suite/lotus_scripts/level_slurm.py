"""
Created on Wed Jul 22 09:09:41 2020

@author: iregou
"""

from __future__ import annotations

import glob
import logging
import os
import subprocess
import sys

from glamod_marine_processing.obs_suite.lotus_scripts import (
    config_array, parser, slurm_preferences)
from glamod_marine_processing.utilities import load_json, read_txt


# %%------------------------------------------------------------------------------
def check_file_exist(files):
    """Check whether file exists."""
    files = [files] if not isinstance(files, list) else files
    for filei in files:
        if not os.path.isfile(filei):
            logging.error(f"File {filei} does not exist. Exiting")
            sys.exit(1)


def check_dir_exit(dirs):
    """Check whether directory exists."""
    dirs = [dirs] if not isinstance(dirs, list) else dirs
    for diri in dirs:
        if not os.path.isdir(diri):
            logging.error(f"Directory {diri} does not exist. Exiting")
            sys.exit(1)


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


def source_dataset(level, release):
    """Get source dataset."""
    if level == "level1a":
        return "datasets"
    return release


# %%------------------------------------------------------------------------------


logging.basicConfig(
    format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
    level=logging.INFO,
    datefmt="%Y%m%d %H:%M:%S",
    filename=None,
)

# Get process coordinates and build paths -------------------------------------
script_config_file = sys.argv[1]
check_file_exist([script_config_file])
script_config = load_json(script_config_file)

release = script_config["abbreviations"]["release"]
update = script_config["abbreviations"]["update"]
dataset = script_config["abbreviations"]["dataset"]
config_files_path = script_config["paths"]["config_files_path"]
release_periods_file = script_config["release_periods_file"]
release_periods_file = os.path.join(config_files_path, release_periods_file)

args = parser.get_parser_args()

LEVEL = script_config["level"]
LEVEL_SOURCE = slurm_preferences.level_source[LEVEL]
if "source_pattern" in script_config.keys():
    SOURCE_PATTERN = script_config["source_pattern"]
else:
    SOURCE_PATTERN = slurm_preferences.source_pattern[LEVEL]

if isinstance(SOURCE_PATTERN, dict):
    SOURCE_PATTERN = SOURCE_PATTERN[dataset]

PYSCRIPT = f"{LEVEL}.py"
MACHINE = script_config["scripts"]["machine"].lower()
overwrite = script_config["overwrite"]

# Get lotus paths
lotus_dir = script_config["paths"]["lotus_scripts_directory"]
scripts_dir = script_config["paths"]["scripts_directory"]
data_dir = script_config["paths"]["data_directory"]
scratch_dir = script_config["paths"]["scratch_directory"]

# Build process specific paths
level_dir = os.path.join(data_dir, release, dataset, LEVEL)
level_source = source_dataset(LEVEL, release)
level_source_dir = os.path.join(data_dir, level_source, dataset, LEVEL_SOURCE)
log_dir = os.path.join(level_dir, "log")

# Get further configuration -----------------------------------------------------------
if script_config["process_list"]:
    process_list = script_config["process_list"]
else:
    process_list_file = script_config["process_list_file"]
    process_list_file = os.path.join(config_files_path, process_list_file)
    check_file_exist([process_list_file])
    process_list = read_txt(process_list_file)

logging.info(f"Periods file used: {release_periods_file}")
logging.info(f"Process deck list: {process_list}")
check_file_exist([release_periods_file])
release_periods = load_json(release_periods_file)

if script_config["year_init"]:
    release_periods["year_init"] = script_config["year_init"]
if script_config["year_end"]:
    release_periods["year_end"] = script_config["year_end"]

# Optionally, add CMD add file
add_file = os.path.join(config_files_path, f"{LEVEL}_cmd_add.json")
if os.path.isfile(add_file):
    script_config["cmd_add_file"] = add_file

# Build array input files -----------------------------------------------------
logging.info("CONFIGURING JOB ARRAYS...")
status = config_array.main(
    level_source_dir,
    SOURCE_PATTERN,
    log_dir,
    script_config,
    release_periods,
    process_list,
    failed_only=args.failed_only,
)
if status != 0:
    logging.error("Creating array inputs")
    sys.exit(1)

# Build jobs ------------------------------------------------------------------
py_path = os.path.join(scripts_dir, PYSCRIPT)
pycommand = f"python {py_path} {data_dir} {release} {update} {dataset}"

# Set default job params
mem = script_config["job_memo_mb"]
t_hh = script_config["job_time_hr"]
t_mm = script_config["job_time_min"]
t = ":".join([t_hh, t_mm, "00"])

logging.info("SUBMITTING ARRAYS...")

for sid_dck in process_list:
    logging.info(f"Creating scripts for {sid_dck}")
    log_diri = os.path.join(log_dir, sid_dck)
    array_size = len(glob.glob(os.path.join(log_diri, "*.input")))
    if array_size == 0:
        logging.warning(f"{sid_dck}: no jobs for partition")
        continue

    job_file = os.path.join(log_diri, sid_dck + ".slurm")
    taskfarm_file = os.path.join(log_diri, sid_dck + ".tasks")

    if LEVEL in slurm_preferences.TaskPNi.keys():
        TaskPNi = slurm_preferences.TaskPNi[LEVEL]
    else:
        memi = script_config.get(sid_dck, {}).get("job_memo_mb")
        memi = mem if not memi else memi
        TaskPNi = min(int(190000.0 / float(memi)), 40)

    if LEVEL in slurm_preferences.nodesi.keys():
        nodesi = slurm_preferences.nodesi[LEVEL]
    else:
        nodesi = array_size // TaskPNi + (array_size % TaskPNi > 0)

    if LEVEL in slurm_preferences.ti.keys():
        ti = slurm_preferences.ti[LEVEL]
    else:
        t_hhi = script_config.get(sid_dck, {}).get("job_time_hr")
        t_mmi = script_config.get(sid_dck, {}).get("job_time_min")
        if t_hhi and t_mmi:
            ti = ":".join([t_hhi, t_mmi, "00"])
        else:
            ti = t

    calc_tasks = False
    with open(taskfarm_file, "w") as fh:
        for i in range(array_size):
            if os.path.isfile(f"{log_diri}/{i+1}.failure"):
                logging.info(f"Task {i+1} failed. Try calculating again.")
                os.remove(f"{log_diri}/{i+1}.failure")
            elif os.path.isfile(f"{log_diri}/{i+1}.success"):
                if overwrite is not True:
                    logging.info(
                        f"Task {i+1} was already successful. Skip calculating again."
                    )
                    continue
                logging.info(
                    f"Task {i+1} was already successful. However, calculate task again since option 'overwrite' was chosen."
                )
                os.remove(f"{log_diri}/{i+1}.success")

            fh.writelines(
                "{0} {1}/{2}.input > {1}/{2}.out 2> {1}/{2}.out; if [ $? -eq 0 ]; "
                "then touch {1}/{2}.success; else touch {1}/{2}.failure; fi  \n".format(
                    pycommand, log_diri, i + 1
                )
            )
            calc_tasks = True

    if calc_tasks is False:
        logging.info("No tasks to be calculated")
        continue

    header = read_txt(os.path.join(lotus_dir, "header", f"slurm_header_{MACHINE}.txt"))

    with open(job_file, "w") as fh:
        for line in header:
            line = eval(line)
            line = f"{line}\n"
            fh.writelines(line)

    logging.info(f"{sid_dck}: launching array")
    logging.info(f"Script {taskfarm_file} was created.")
    if script_config["submit_jobs"] is True:
        process = f"jid=$(sbatch {job_file} | cut -f 4 -d' ') && echo $jid"
        logging.info(f"process launching: {process}")
        jid = launch_process(process)
    else:
        subprocess.call(["/bin/chmod", "u+x", taskfarm_file], shell=False)
        if script_config["run_jobs"] is True:
            logging.info("Run jobs interactively.")
            subprocess.call(["/bin/sh", taskfarm_file], shell=False)
            logging.info(f"Check whether jobs was successful: {log_diri}")
        elif script_config["parallel_jobs"] is True:
            logging.info("Run jobs interactively in parallel.")
            subprocess.call(
                [
                    "/bin/parallel",
                    "--jobs",
                    script_config["n_max_jobs"],
                    "::::",
                    taskfarm_file,
                ],
                shell=False,
            )
