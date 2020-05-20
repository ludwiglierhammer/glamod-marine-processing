#!/bin/bash


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

run_id=$(basename $script_config_file .json)
out_dir=$data_directory/user_manual/release_summaries/$release

python $um_code_directory/data_summaries/sd_monthly_grids_config_array.py $data_directory $release $dataset $level $script_config_file $data_periods_file $process_list_file $failed_only

# for sid_dck in $(awk '{print $1}' $process_list)
# do
#   sid_dck_log_dir=$out_dir/log/$sid_dck
#   arrl=$(ls -1q $sid_dck_log_dir/"*-"$run_id".input" | wc -l)
#
#   jobid=$(nk_jobid bsub -J $sid_dck"[1-$arrl]" -oo $sid_dck_log_dir/"%I-"$run_id".o" -eo $sid_dck_log_dir/"%I-"$run_id".o" -q short-serial -W $job_time_hhmm -M $job_memo_mbi -R "rusage[mem=$job_memo_mbi]" \
#   python $scripts_directory/$pyscript $sid_dck_log_dir/\$LSB_JOBINDEX"-"$run_id".input")
