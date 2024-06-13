"""Quality control SLURM module."""

from __future__ import annotations

import logging
import os
import subprocess
import sys

from glamod_marine_processing.qc_suite.lotus_scripts import parser, slurm_preferences
from glamod_marine_processing.utilities import load_json, read_txt

# %%------------------------------------------------------------------------------


def launch_process(process):
    """Lauch process."""
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


# %%------------------------------------------------------------------------------

logging.basicConfig(
    format="%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s",
    level=logging.INFO,
    datefmt="%Y%m%d %H:%M:%S",
    filename=None,
)

# %%------------------------------------------------------------------------------

mode = parser.get_parser_args().mode
scriptfn = slurm_preferences.scriptfn[mode]
JOBSFN = "jobs2.json"

NODES = slurm_preferences.nodesi[mode]
TI = slurm_preferences.ti[mode]
TasksPN = slurm_preferences.TaskPNi[mode]

# %%------------------------------------------------------------------------------

configfile = os.path.abspath(sys.argv[1])
if not os.path.isfile(configfile):
    sys.exit(f"Configuration file not found at: {configfile}")
script_config = load_json(configfile)
machine = script_config["machine"]

# all including path
scripts_directory = script_config["paths"]["scripts_directory"]
lotus_script_directory = script_config["paths"]["lotus_scripts_directory"]
config_directory = script_config["paths"]["config_directory"]
logdir = slurm_preferences.logdir[mode]
logdir = script_config["paths"][logdir]
pyscript = os.path.join(scripts_directory, scriptfn)
jobsfile = os.path.join(config_directory, JOBSFN)
overwrite = script_config["overwrite"]

if not os.path.isfile(pyscript):
    sys.exit(f"Python script not found at: {pyscript}")
if not os.path.isfile(jobsfile):
    sys.exit(f"Jobs file not found at: {jobsfile}")
if not os.path.isdir(logdir):
    sys.exit(f"Log directory not found at: {logdir}")

# %%------------------------------------------------------------------------------

job_ids = list(range(85, 97))

taskfile = os.path.join(logdir, slurm_preferences.taskfile[mode])
slurmfile = os.path.join(logdir, slurm_preferences.slurmfile[mode])

jobs_torun = []
for job_id in job_ids:
    if os.path.isfile(os.path.join(logdir, f"{job_id}.success")):
        logging.info(
            f"Job {job_id} previously successful, job not rerun. Remove file 'i.success' to force rerun."
        )
        job_ids.remove(job_id)
    else:
        jobs_torun.append(job_id)

calc_tasks = False
with open(taskfile, "w") as fn:
    for job_id in jobs_torun:
        if os.path.isfile(os.path.join(logdir, f"{job_id}.failure")):
            logging.info(f"Deleting {job_id}.failure file for a fresh start")
            os.remove(os.path.join(logdir, f"{job_id}.failure"))
        if os.path.isfile(os.path.join(logdir, f"{job_id}.success")):
            if overwrite is not True:
                logging.info(
                    f"Task {job_id} was already successful. Skip calculating again."
                )
                continue
            logging.info(
                f"Task {job_id} was already successful. However, calculate task again since option 'overwrite' was chosen."
            )
            os.remove(os.path.join(logdir, f"{job_id}.success"))
        calc_tasks = True
        fn.writelines(
            "python3 {0} -jobs {1} -job_index {2} -config {3} -tracking > {4}/{2}.out 2> {4}/{2}.err;"
            " if [ $? -eq 0 ]; then touch {4}/{2}.success; else touch {4}/{2}.failure; fi \n".format(
                pyscript, jobsfile, job_id, configfile, logdir
            )
        )

if calc_tasks is False:
    logging.info("No tasks to be calculated.")
    sys.exit()

header = read_txt(
    os.path.join(lotus_script_directory, "header", f"slurm_header_{machine}.txt")
)

with open(slurmfile, "w") as fh:
    for line in header:
        line = eval(line)
        line = f"{line}\n"
        fh.writelines(line)

if script_config["submit_jobs"] is True:
    logging.info(f"{taskfile}: launching taskfarm")
    process = f"jid=$(sbatch {slurmfile}) && echo $jid"
    logging.info(f"process launching: {process}")
    jid = launch_process(process)
else:
    logging.info(f"{taskfile}: create script")
    logging.info(f"Script {slurmfile} was created.")
    if script_config["run_jobs"] is True:
        logging.info("Run interactively.")
        os.system(f"chmod u+x {taskfile}")
        os.system(f"{taskfile}")
        logging.info(f"Check whether jobs was successful: {logdir}")
