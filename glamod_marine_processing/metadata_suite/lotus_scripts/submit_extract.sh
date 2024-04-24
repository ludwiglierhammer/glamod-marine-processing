#!/bin/bash
#BSUB -J extract_[1-660]
#BSUB -q short-serial
#BSUB -o ./extract_logs/%J_%I.out
#BSUB -e ./extract_logs/%J_%I.err
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000

source ./setenv0.sh
if [ -f extract_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'extract_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python3 ${scripts_directory}/extract_for_cds.py  -config ${code_directory}/config/config_lotus.json -schema\
        ${code_directory}/config/master.json -index ${LSB_JOBINDEX}
    if [ $? -eq 0 ]
    then
	    touch extract_${LSB_JOBINDEX}.success
        bsub -w "done(${LSB_JOBID})" mv ./extract_logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./extract_logs/successful/
        if [ -f  extract_${LSB_JOBINDEX}.failed ]
        then
            rm extract_${LSB_JOBINDEX}.failed
        fi
    else
	    touch extract_${LSB_JOBINDEX}.failed
        bsub -w "done(${LSB_JOBID})" mv ./extract_logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./extract_logs/failed/
	fi
fi
