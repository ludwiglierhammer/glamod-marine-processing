#!/bin/bash

#. FUNCTIONS -------------------------------------------------------------------
# Get JOB
function nk_jobid {
    output=$($*)
    echo $output | head -n1 | cut -d'<' -f2 | cut -d'>' -f1
}
# ------------------------------------------------------------------------------
source ../setpaths.sh
source ../setenv0.sh

# Here make sure we are using fully expanded paths, as some may be passed to a config file
release=$1
dataset=$2
level=$3
script_config_file=$(readlink --canonicalize  $4)
data_periods_file=$(readlink --canonicalize  $5)
process_list_file=$(readlink --canonicalize  $6)
failed_only=$7



pyconfig=$um_code_directory/data_summaries/sd_monthly_grids_config_array.py
pyscript=$um_code_directory/data_summaries/sd_monthly_grids.py
pyhdlr=$um_code_directory/data_summaries/process_array_output_hdlr.py
run_id=$(basename $script_config_file .json)
out_dir=$data_directory/user_manual/release_summaries/$release/$dataset

job_time_hhmm=00:20
job_memo_mbi=8000

echo "JOBS CONFIGURATION"
echo 

python $pyconfig $data_directory $release $dataset $level $script_config_file $data_periods_file $process_list_file $failed_only

echo "LAUNCHING JOBS"
for sid_dck in $(awk '{print $1}' $process_list_file)
do
   sid_dck_log_dir=$out_dir/log/$sid_dck
   arrl=$(ls -1q $sid_dck_log_dir/*-$run_id".input" 2> /dev/null | wc -l)
   
   if [[ "$arrl" == '0' ]]
   then
        echo "No jobs found for $sid_dck"
   	continue
   else
        echo "Launching $sid_dck array"
   fi
 


   jobid=$(nk_jobid bsub -J $sid_dck"[1-$arrl]" -oo $sid_dck_log_dir/"%I-"$run_id".o" -eo $sid_dck_log_dir/"%I-"$run_id".o" -q short-serial -W $job_time_hhmm -M $job_memo_mbi -R "rusage[mem=$job_memo_mbi]" python $pyscript $sid_dck_log_dir/\$LSB_JOBINDEX"-"$run_id".input")

   bsub -J OK"[1-$arrl]" -w "done($jobid[*])" -oo $sid_dck_log_dir/"%I-"$run_id".ho" -eo $sid_dck_log_dir/"%I-"$run_id".ho" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" \
   python $pyhdlr $sid_dck_log_dir/\$LSB_JOBINDEX"-"$run_id".input" 0 1

   bsub -J ER"[1-$arrl]" -w "exit($jobid[*])" -oo $sid_dck_log_dir/"%I-"$run_id".ho" -eo $sid_dck_log_dir/"%I-"$run_id".ho" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" \
   python $pyhdlr $sid_dck_log_dir/\$LSB_JOBINDEX"-"$run_id".input" 1 1

done
