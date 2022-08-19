#!/bin/bash 
#BSUB -J moqc_[643-645]
#BSUB -q short-serial 
#BSUB -o ./logs_qc/%J_%I.out 
#BSUB -e ./logs_qc/%J_%I.err 
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000       

source ./setenv_3.7.3.sh
if [ -f qc_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'qc_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python3 ${scripts_directory}/marine_qc.py -jobs ${code_directory}/config/jobs.json -job_index ${LSB_JOBINDEX} \
        -config ${code_directory}/config/configuration.txt -tracking
    if [ $? -eq 0 ] 
    then
	    touch qc_${LSB_JOBINDEX}.success
        if [ -f qc_${LSB_JOBINDEX}.failed ]
        then
            rm qc_${LSB_JOBINDEX}.failed
        fi
        echo "submitting clean up job: mv ./logs_qc/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc/successful/"
        bsub -w "done(${LSB_JOBID})" mv ./logs_qc/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc/successful/
    else
	    touch qc_${LSB_JOBINDEX}.failed
        echo "submitting clean up job: mv ./logs_qc/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc/failed/"
        bsub -w "done(${LSB_JOBID})" mv ./logs_qc/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_qc/failed/                
	fi
fi
