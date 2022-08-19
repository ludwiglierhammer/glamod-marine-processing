#!/bin/bash 
#SBATCH --job-name=moqchr
#SBATCH --array=643-645
#SBATCH --partition=short-serial
#SBATCH -o ./logs_qc_hr/%A_%a.out 
#SBATCH -e ./logs_qc_hr/%A_%a.err 
#SBATCH --time=12:00:00
#SBATCH --mem=64000
       
source ./setenv0.sh
if [ -f qc_hr_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'qc_hr_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python3 ${scripts_directory}/marine_qc_hires.py -jobs ${code_directory}/config/jobs.json -job_index ${LSB_JOBINDEX} \
        -config ${code_directory}/config/configuration.txt -tracking
    if [ $? -eq 0 ] 
    then
	    touch qc_hr_${LSB_JOBINDEX}.success
        if [ -f qc_hr_${LSB_JOBINDEX}.failed ]
        then
            rm qc_hr_${LSB_JOBINDEX}.failed
        fi
        echo "submitting clean up job: mv ./logs_qc_hr/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc_hr/successful/"
        bsub -w "done(${LSB_JOBID})" mv ./logs_qc_hr/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc_hr/successful/
    else
	    touch qc_hr_${LSB_JOBINDEX}.failed
        echo "submitting clean up job: mv ./logs_qc_hr/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc_hr/failed/"
        bsub -w "done(${LSB_JOBID})" mv ./logs_qc_hr/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc_hr/failed/                
	fi
fi
