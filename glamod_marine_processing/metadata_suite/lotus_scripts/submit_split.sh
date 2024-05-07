scripts_directory=$1
code_directory=$2
release_directory=$3
config_lotus=$4

if [ -f split_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'split_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python ${scripts_directory}/split_pub47.py -config ${code_directory}/config/config_lotus.json \
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
