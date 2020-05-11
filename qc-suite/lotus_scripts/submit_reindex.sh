#!/bin/bash
#BSUB -J jobs_[1-1000]
#BSUB -q short-serial
#BSUB -o ./logs_reindex/%J_%I.out
#BSUB -e ./logs_reindex/%J_%I.err
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000
touch reindex_${LSB_JOBINDEX}.fail
source setenv_3.7.3.sh
python3 ${scripts_directory}/reindex_tracking.py  -jobindex ${LSB_JOBINDEX} \
  -lotus_id ${LSB_JOBINDEX} -poolsize 1000 -source ${home_directory}/data/r092019/ICOADS_R3.0.0T/metoffice_qc/dbuoy_track/MetOffice_Tracking_QC\
  -dest ${working_directory}/tracking/

if [ $? -eq 0 ]
then
  rm reindex_${LSB_JOBINDEX}.fail
  touch reindex_${LSB_JOBINDEX}.success
fi
