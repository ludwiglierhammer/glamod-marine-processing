scripts_directory=$1
code_directory=$2
release_directory=$3
log_directory=$4
config_lotus=$5
LSB_JOBINDEX=1
if [ -f ${release_directory}/split_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'split_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python ${scripts_directory}/split_pub47.py -config ${config_lotus} \
        -jobs ${code_directory}/config/jobs.json -start ${LSB_JOBINDEX} -end ${LSB_JOBINDEX} \
        -tag split_${LSB_JOBINDEX} -log ${log_directory}
    if [ $? -eq 0 ]
    then
	    touch ${release_directory}/split_${LSB_JOBINDEX}.success
        #bsub -w "done(${LSB_JOBID})" mv ./logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs/successful/
    else
	    touch ${release_directory}/split_${LSB_JOBINDEX}.failed
        #bsub -w "done(${LSB_JOBID})" mv ./logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./logs/failed/
	fi
fi
