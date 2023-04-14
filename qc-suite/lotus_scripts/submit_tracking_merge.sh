#!/bin/bash 
#SBATCH --job-name=moqc
#SBATCH --array=1-2
#SBATCH --partition=short-serial
#SBATCH -o ./logs_trck/%A_%a.out 
#SBATCH -e ./logs_trck/%A_%a.err 
#SBATCH --time=12:00:00
#SBATCH --mem=64000


touch merge_${SLURM_ARRAY_TASK_ID}.fail
#source setenv_3.7.3.sh
source /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/setenv0.sh

python3 /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/scripts/merge_tracking.py  -index ${SLURM_ARRAY_TASK_ID} \
  -source ${working_directory}/tracking/ \
  -dest ${working_directory}/tracking/

if [ $? -eq 0 ]
then
  rm merge_${SLURM_ARRAY_TASK_ID}.fail
  touch merge_${SLURM_ARRAY_TASK_ID}.success
fi
