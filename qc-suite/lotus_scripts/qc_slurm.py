#!/bin/bash python3

#make sure setenv0.sh is sourced before
#about 3,5h per data month (tested in 2021), 4 jobs per node (ca. 40Gb ram per job)

import sys
import os
import json
import subprocess
import logging


#%%------------------------------------------------------------------------------

def launch_process(process):

    proc = subprocess.Popen([process],shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    jid_by, err = proc.communicate()
    if len(err)>0:
        logging.error('Error launching process. Exiting')
        logging.info('Error is: {}'.format(err))
        sys.exit(1)
    jid = jid_by.decode('UTF-8').rstrip()

    return jid.split(' ')[-1]

#%%------------------------------------------------------------------------------

logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)

#%%------------------------------------------------------------------------------

SCRIPTFN = 'marine_qc.py'
JOBSFN = 'jobs2.json'
CONFIGFN = 'configuration_r3.0.2.txt'

NODES = 1         #3
TI = '08:00:00'   #'12:00:00'
#MEM = 191999       #64000
#memory request replaced by limiting tasks per node to 4
TasksPN = 4
#%%------------------------------------------------------------------------------


#all including path
scripts_directory = os.getenv('scripts_directory')
config_directory = os.getenv('config_directory')
logdir = os.getenv('qc_log_directory')

pyscript = os.path.join(scripts_directory, SCRIPTFN)
jobsfile = os.path.join(config_directory, JOBSFN)
configfile = os.path.join(config_directory, CONFIGFN)

if not os.path.isfile(pyscript):
    sys.exit('Python script not found at: {}'.format(pyscript))
if not os.path.isfile(jobsfile):
    sys.exit('Jobs file not found at: {}'.format(jobsfile))
if not os.path.isfile(configfile):
    sys.exit('Configuration file not found at: {}'.format(configfile))
if not os.path.isdir(logdir):
    sys.exit('Log directory not found at: {}'.format(logdir))


#%%------------------------------------------------------------------------------


#source ../setenv0.sh

job_ids = list(range(73,85))

taskfile = os.path.join(logdir, 'qc.tasks')
slurmfile = os.path.join(logdir, 'qc.slurm')
jobs_torun = []

for job_id in job_ids:
    if os.path.isfile(os.path.join(logdir,'{}.success'.format(job_id))):
        logging.info("Job {0} previously successful, job not rerun. Remove file '{0}.success' to force rerun.".format(job_id))
    else:
        jobs_torun.append(job_id)


with open(taskfile, 'w') as fn:
    for job_id in jobs_torun:
        if os.path.isfile(os.path.join(logdir,'{}.failure'.format(job_id))):
             logging.info('Deleting {}.failure file for a fresh start'.format(job_id))
             os.remove(os.path.join(logdir,'{}.failure'.format(job_id)))

        fn.writelines('python3 {0} -jobs {1} -job_index {2} -config {3} -tracking > {4}/{2}.out 2> {4}/{2}.err; if [ $? -eq 0 ]; then touch {4}/{2}.success; else touch {4}/{2}.failure; fi \n'\
              .format(pyscript, jobsfile, job_id, configfile, logdir))


with open(slurmfile,'w') as fh:
        fh.writelines('#!/bin/bash\n')
        fh.writelines('#SBATCH --job-name=qc.job\n')
        fh.writelines('#SBATCH --output={}/%a.out\n'.format(logdir))
        fh.writelines('#SBATCH --error={}/%a.err\n'.format(logdir))
        fh.writelines('#SBATCH --time={}\n'.format(TI))
        fh.writelines('#SBATCH --nodes={}\n'.format(NODES))
        #fh.writelines('#SBATCH --mem={}\n'.format(MEM))
        fh.writelines('#SBATCH -A glamod\n')
        fh.writelines('module load taskfarm\n')
        fh.writelines('export TASKFARM_PPN={}\n'.format(TasksPN))
        fh.writelines('taskfarm {}\n'.format(taskfile))

logging.info('{}: launching taskfarm'.format(taskfile))
process = "jid=$(sbatch {}) && echo $jid".format(slurmfile)
jid = launch_process(process)
