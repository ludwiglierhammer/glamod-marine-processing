scripts_directory=$1
code_directory=$2
release_directory=$3
config_lotus=$4
LSB_JOBINDEX=1

if [ -f ${release_directory}/merge_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'merge_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python ${scripts_directory}/merge_countries.py -config ${config_lotus} \
        -jobs ${code_directory}/config/jobs.json -countries ${code_directory}/config/countries.json -index ${LSB_JOBINDEX}
    if [ $? -eq 0 ]
    then
	    touch ${release_directory}/merge_${LSB_JOBINDEX}.success
        #bsub -w "done(${LSB_JOBID})"
        mv ./merge_logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./merge_logs/successful/
        if [ -f  merge_${LSB_JOBINDEX}.failed ]
        then
            rm merge_${LSB_JOBINDEX}.failed
        fi
    else
	    touch ${release_directory}/merge_${LSB_JOBINDEX}.failed
        #bsub -w "done(${LSB_JOBID})"
        mv ./merge_logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./merge_logs/failed/
	fi
fi

if [ ${LSB_JOBINDEX} == 1 ]
then
#bsub -w "done(${LSB_JOBID})"
  python ${scripts_directory}/combine_master_files.py -config ${config_lotus} \
    -countries ${code_directory}/config/countries.json
fi
