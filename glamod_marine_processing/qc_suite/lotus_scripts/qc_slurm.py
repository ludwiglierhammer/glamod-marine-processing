"""Quality control SLURM module."""

# make sure setenv0.sh is sourced before
# about 5h per data month (tested in 2021), 4 jobs per node (ca. 40Gb ram per job)

from __future__ import annotations

import logging
import os
import subprocess
import sys

from glamod_marine_processing.utilities import load_json

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

SCRIPTFN = "marine_qc.py"
JOBSFN = "jobs2.json"
# CONFIGFN = 'configuration_r3.0.2.txt'
# CONFIGFN = 'config_r3.0.2_release_6.0.txt'

NODES = 2  # 3
TI = "06:00:00"  #'12:00:00'
# MEM = 191999       #64000
# memory request replaced by limiting tasks per node to 4
TasksPN = 3
# %%------------------------------------------------------------------------------

configfile = sys.argv[1]
if not os.path.isfile(configfile):
    sys.exit(f"Configuration file not found at: {configfile}")
script_config = load_json(configfile)

# all including path
scripts_directory = script_config["paths"]["scripts_directory"]
config_directory = script_config["paths"]["config_directory"]
logdir = script_config["paths"]["qc_log_directory"]
pyscript = os.path.join(scripts_directory, SCRIPTFN)
jobsfile = os.path.join(config_directory, JOBSFN)

if not os.path.isfile(pyscript):
    sys.exit(f"Python script not found at: {pyscript}")
if not os.path.isfile(jobsfile):
    sys.exit(f"Jobs file not found at: {jobsfile}")
if not os.path.isdir(logdir):
    sys.exit(f"Log directory not found at: {logdir}")


# %%------------------------------------------------------------------------------


# source ../setenv0.sh

# job_ids = list(range(73,85))#2021
job_ids = list(range(85, 97))  # 2022


taskfile = os.path.join(logdir, "qc.tasks")
slurmfile = os.path.join(logdir, "qc.slurm")
jobs_torun = []

for job_id in job_ids:
    if os.path.isfile(os.path.join(logdir, f"{job_id}.success")):
        logging.info(
            "Job {0} previously successful, job not rerun. Remove file '{0}.success' to force rerun.".format(
                job_id
            )
        )
    else:
        jobs_torun.append(job_id)


with open(taskfile, "w") as fn:
    for job_id in jobs_torun:
        if os.path.isfile(os.path.join(logdir, f"{job_id}.failure")):
            logging.info(f"Deleting {job_id}.failure file for a fresh start")
            os.remove(os.path.join(logdir, f"{job_id}.failure"))

        fn.writelines(
            "python3 {0} -jobs {1} -job_index {2} -config {3} -tracking > {4}/{2}.out 2> {4}/{2}.err; if [ $? -eq 0 ];"
            " then touch {4}/{2}.success; else touch {4}/{2}.failure; fi \n".format(
                pyscript, jobsfile, job_id, configfile, logdir
            )
        )


with open(slurmfile, "w") as fh:
    fh.writelines("#!/bin/bash\n")
    fh.writelines("#SBATCH --job-name=qc.job\n")
    fh.writelines(f"#SBATCH --output={logdir}/%a.out\n")
    fh.writelines(f"#SBATCH --error={logdir}/%a.err\n")
    fh.writelines(f"#SBATCH --time={TI}\n")
    fh.writelines(f"#SBATCH --nodes={NODES}\n")
    # fh.writelines('#SBATCH --mem={}\n'.format(MEM))
    fh.writelines("#SBATCH -A glamod\n")
    fh.writelines("module load taskfarm\n")
    fh.writelines(f"export TASKFARM_PPN={TasksPN}\n")
    fh.writelines(f"taskfarm {taskfile}\n")

    if script_config["submit_jobs"] is True:
        logging.info(f"{taskfile}: launching taskfarm")
        process = f"jid=$(sbatch {slurmfile}) && echo $jid"
        logging.info(f"process launching: {process}")
        jid = launch_process(process)
    else:
        logging.info(f"{taskfile}: create script")
        logging.info(f"Script {slurmfile} was created.")
