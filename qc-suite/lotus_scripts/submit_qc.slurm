#!/bin/bash 
#SBATCH --job-name=moqc
#SBATCH --array=1-90
#SBATCH --partition=short-serial
#SBATCH -o ./logs_qc/%A_%a.out 
#SBATCH -e ./logs_qc/%A_%a.err 
#SBATCH --time=12:00:00
#SBATCH --mem=64000

source ./setenv0.sh
if [ -f qc_${SLURM_ARRAY_TASK_ID}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'qc_${SLURM_ARRAY_TASK_ID}.success' to force rerun."
    echo ""
else
    python3 ${scripts_directory}/marine_qc.py -jobs ${code_directory}/config/jobs2.json -job_index ${SLURM_ARRAY_TASK_ID} \
        -config ${code_directory}/config/configuration.txt -tracking
    if [ $? -eq 0 ] 
    then
	    touch qc_${SLURM_ARRAY_TASK_ID}.success
        if [ -f qc_${SLURM_ARRAY_TASK_ID}.failed ]
        then
            rm qc_${SLURM_ARRAY_TASK_ID}.failed
        fi
        echo "submitting clean up job: mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/successful/"
        bsub -w "done(${SLURM_JOBID})" mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/successful/
    else
	    touch qc_${SLURM_ARRAY_TASK_ID}.failed
        echo "submitting clean up job: mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/failed/"
        bsub -w "done(${SLURM_JOBID})" mv ./logs_qc/${SLURM_JOBID}_${SLURM_ARRAY_TASK_ID}.* ./logs_qc/failed/                
	fi
fi
