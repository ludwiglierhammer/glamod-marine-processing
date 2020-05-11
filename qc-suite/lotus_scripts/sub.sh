#!/bin/bash 
#BSUB -J jobs_[1-828]
#BSUB -q short-serial 
#BSUB -o ./logs/%J_%I.out 
#BSUB -e ./logs/%J_%I.err 
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000       

python3 /gws/smf/j04/c3s311a_lot2/dyb/qc_code/preprocess.py -jobs jobs.json -job_index ${LSB_JOBINDEX}
