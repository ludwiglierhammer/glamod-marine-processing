#!/bin/bash
#BSUB -J split_[1-83]
#BSUB -q short-serial
#BSUB -o ./logs/%J_%I.out
#BSUB -e ./logs/%J_%I.err
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000

source ./setenv0.sh
if [ -f split_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'split_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python3 ${scripts_directory}/split_pub47.py -config ${code_directory}/config/config_lotus.json \
        -jobs ${code_directory}/config/jobs.json -start ${LSB_JOBINDEX} -tag split_${LSB_JOBINDEX} \
        -log ./logs2/
    if [ $? -eq 0 ]
    then
	    touch split_${LSB_JOBINDEX}.success
        bsub -w "done(${LSB_JOBID})" mv ./logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs/successful/
    else
	    touch split_${LSB_JOBINDEX}.failed
        bsub -w "done(${LSB_JOBID})" mv ./logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs/failed/
	fi
fi
