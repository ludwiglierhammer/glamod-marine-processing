#!/bin/bash
#BSUB -J jobs_[1-360]
#BSUB -q short-serial
#BSUB -o ./logs_merge/%J_%I.out
#BSUB -e ./logs_merge/%J_%I.err
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000
touch merge_${LSB_JOBINDEX}.fail
source setenv_3.7.3.sh
python3 ${scripts_directory}/merge_tracking.py  -index ${LSB_JOBINDEX} \
  -source ${working_directory}/tracking/ \
  -dest ${working_directory}/tracking/

if [ $? -eq 0 ]
then
  rm merge_${LSB_JOBINDEX}.fail
  touch merge_${LSB_JOBINDEX}.success
fi
