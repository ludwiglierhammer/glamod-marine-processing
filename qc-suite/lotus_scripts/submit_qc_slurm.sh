#!/bin/bash 
#SBATCH --job-name=moqc
#SBATCH --array=1-84
#SBATCH --partition=short-serial
#SBATCH -o ./logs_qc/%A_%a.out 
#SBATCH -e ./logs_qc/%A_%a.err 
#SBATCH --time=12:00:00
#SBATCH --mem=64000

source /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/setenv0.sh

if [ -f qc_${SLURM_ARRAY_TASK_ID}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'qc_${SLURM_ARRAY_TASK_ID}.success' to force rerun."
    echo ""
else
    python3 /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/scripts/marine_qc.py -jobs /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/config/jobs2.json -job_index ${SLURM_ARRAY_TASK_ID} \
        -config /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/config/configuration_r3.0.2.txt -tracking
    if [ $? -eq 0 ] 
    then
	    touch qc_${SLURM_ARRAY_TASK_ID}.success
        if [ -f qc_${SLURM_ARRAY_TASK_ID}.failed ]
        then
            rm qc_${SLURM_ARRAY_TASK_ID}.failed
        fi
        echo "submitting clean up job: mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/successful/"
        echo "done(${SLURM_JOBID})" mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/successful/
    else
	    touch qc_${SLURM_ARRAY_TASK_ID}.failed
        echo "submitting clean up job: mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/failed/"
        echo "done(${SLURM_JOBID})" mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/failed/                
	fi
fi
