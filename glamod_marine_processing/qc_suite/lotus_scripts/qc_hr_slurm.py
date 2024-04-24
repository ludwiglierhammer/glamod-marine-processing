"""Quality control (hr) SLUM module."""

# make sure setenv0.sh is sourced before

from __future__ import annotations

import logging
import os
import subprocess
import sys

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

SCRIPTFN = "marine_qc_hires.py"
JOBSFN = "jobs2.json"
CONFIGFN = "configuration_r3.0.2.txt"

NODES = 1  # 3
TI = "09:00:00"  #'12:00:00'
# MEM = 64000      #64000
TasksPN = 4

# about 1:10h per data month (2021) per task
# %%------------------------------------------------------------------------------

configfile = os.path.abspath(sys.argv[1])


# all including path
scripts_directory = os.getenv("scripts_directory")
config_directory = os.getenv("config_directory")
logdir = os.getenv("qc_hr_log_directory")

pyscript = os.path.join(scripts_directory, SCRIPTFN)
jobsfile = os.path.join(config_directory, JOBSFN)
# configfile = os.path.join(config_directory, CONFIGFN)

if not os.path.isfile(pyscript):
    sys.exit(f"Python script not found at: {pyscript}")
if not os.path.isfile(jobsfile):
    sys.exit(f"Jobs file not found at: {jobsfile}")
if not os.path.isfile(configfile):
    sys.exit(f"Configuration file not found at: {configfile}")
if not os.path.isdir(logdir):
    sys.exit(f"Log directory not found at: {logdir}")


# %%------------------------------------------------------------------------------


# source ../setenv0.sh
taskfile = os.path.join(logdir, "qc_hr.tasks")
slurmfile = os.path.join(logdir, "qc_hr.slurm")

# job_ids = list(range(73,85))#2021
job_ids = list(range(85, 97))  # 2022

for job_id in job_ids:
    if os.path.isfile(os.path.join(logdir, f"{job_id}.success")):
        logging.info(
            f"Job {job_id} previously successful, job not rerun. Remove file 'i.success' to force rerun."
        )
        job_ids.remove(job_id)


with open(taskfile, "w") as fn:
    for job_id in job_ids:
        if os.path.isfile(os.path.join(logdir, f"{job_id}.failure")):
            logging.info(f"Deleting {job_id}.failure file for a fresh start")
            os.remove(os.path.join(logdir, f"{job_id}.failure"))

        fn.writelines(
            "python3 {0} -jobs {1} -job_index {2} -config {3} -tracking > {4}/{2}.out 2> {4}/{2}.err;"
            " if [ $? -eq 0 ]; then touch {4}/{2}.success; else touch {4}/{2}.failure; fi \n".format(
                pyscript, jobsfile, job_id, configfile, logdir
            )
        )


with open(slurmfile, "w") as fh:
    fh.writelines("#!/bin/bash\n")
    fh.writelines("#SBATCH --job-name=qc_hr.job\n")
    fh.writelines(f"#SBATCH --output={logdir}/%a.out\n")
    fh.writelines(f"#SBATCH --error={logdir}/%a.err\n")
    fh.writelines(f"#SBATCH --time={TI}\n")
    fh.writelines(f"#SBATCH --nodes={NODES}\n")
    # fh.writelines('#SBATCH --mem={}\n'.format(MEM))
    fh.writelines("#SBATCH -A glamod\n")
    fh.writelines(f"export TASKFARM_PPN={TasksPN}\n")
    fh.writelines("module load taskfarm\n")
    fh.writelines(f"taskfarm {taskfile}\n")

logging.info(f"{taskfile}: launching taskfarm")
process = f"jid=$(sbatch {slurmfile}) && echo $jid"
jid = launch_process(process)
