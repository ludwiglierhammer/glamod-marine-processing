#!/bin/bash 
#BSUB -J moqchr_[1-828]
#BSUB -q short-serial 
#BSUB -o ./logs_qc_hr/%J_%I.out 
#BSUB -e ./logs_qc_hr/%J_%I.err 
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000       

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
