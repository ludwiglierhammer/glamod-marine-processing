#!/bin/bash
#BSUB -J jobs_[1-396]
#BSUB -q short-serial
#BSUB -o ./logs_merge_lvl1e/%J_%I.out
#BSUB -e ./logs_merge_lvl1e/%J_%I.err
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000
touch merge_lvl1e_${LSB_JOBINDEX}.fail
source setenv_3.7.3.sh
python3 ${scripts_directory}/merge_level1e.py  -index ${LSB_JOBINDEX} \
  -source ${working_directory}/tracking/ \
  -cdmpath ${home_directory}/data/r092019/ICOADS_R3.0.0T/

if [ $? -eq 0 ]
then
  rm merge_lvl1e_${LSB_JOBINDEX}.fail
  touch merge_lvl1e_${LSB_JOBINDEX}.success
fi
