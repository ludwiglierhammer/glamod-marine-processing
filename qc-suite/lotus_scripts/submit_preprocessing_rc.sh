#!/bin/bash 
#BSUB -J preprocessing_[1-828]
#BSUB -q short-serial 
#BSUB -o ./logs_pp/%J_%I.out 
#BSUB -e ./logs_pp/%J_%I.err 
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000       

# 1 - 840
LSB_JOBINDEX=1
source ./setenv0.sh
if [ -f preprocess_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'preprocess_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python3 ${scripts_directory}/preprocess_rc.py -jobs ${jobs_directory} -job_index ${LSB_JOBINDEX} \
        -schema ${code_directory}/config/schemas/imma/imma.json -code_tables ${code_directory}/config/schemas/imma/code_tables/ \
        -source $data_directory -corrections ${corrections_directory} \
        -destination ${working_directory}/corrected_data/
    if [ $? -eq 0 ] 
    then
	    touch preprocess_${LSB_JOBINDEX}.success
        if [ -f preprocess_${LSB_JOBINDEX}.failed ]
        then
            rm preprocess_${LSB_JOBINDEX}.failed
        fi
        echo "submitting clean up job: mv ./logs_pp/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_pp/successful/"
        bsub -w "done(${LSB_JOBID})" mv ./logs_pp/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_pp/successful/
    else
	    touch preprocess_${LSB_JOBINDEX}.failed
        echo "submitting clean up job: mv ./logs_pp/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_pp/failed/"
        bsub -w "done(${LSB_JOBID})" mv ./logs_pp/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs_pp/failed/                
	fi
fi
