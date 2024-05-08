scripts_directory=$1
code_directory=$2
release_directory=$3
config_lotus=$4
LSB_JOBINDEX=1

if [ -f ${release_directory}/extract_${LSB_JOBINDEX}.success ]
then
    echo ""
    echo "Job previously successful, job not rerun. Remove file 'extract_${LSB_JOBINDEX}.success' to force rerun."
    echo ""
else
    python ${scripts_directory}/extract_for_cds.py  -config ${config_lotus} -schema\
        ${code_directory}/config/master.json -index ${LSB_JOBINDEX}
    if [ $? -eq 0 ]
    then
	    touch ${release_directory}/extract_${LSB_JOBINDEX}.success
        #bsub -w "done(${LSB_JOBID})"
        mv ./extract_logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./extract_logs/successful/
        if [ -f  extract_${LSB_JOBINDEX}.failed ]
        then
            rm extract_${LSB_JOBINDEX}.failed
        fi
    else
	    touch ${release_directory}/extract_${LSB_JOBINDEX}.failed
        #bsub -w "done(${LSB_JOBID})"
        mv ./extract_logs/${LSB_JOBID}_${LSB_JOBINDEX}.* ./extract_logs/failed/
	fi
fi
