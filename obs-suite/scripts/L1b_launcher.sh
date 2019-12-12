#!/bin/bash
# Sends a bsub array of jobs for every sid-deck listed in a the input file
# to run the level1b conversion
#
# Within the sid-deck array, a subjob is only submitted if the corresponding
# source level (level1a) monthly file is available.
#
# bsub input, error and output files are initially located in
# <scratch_dir>/level1b/sid_deck
#
# Main paths are set sourcing r092009_setenv0.sh
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./L1b_launcher.sh release update datasource sid_deck_list_file l1b_config_file
#
# Devel notes:
# Need to rethink how regrouping is launched. Seems it is only launched for yyyy-mm where
# level1a data is avail. How about after datetime corrections having data in yyyy-mm where
# no data was avail in level1a???



source setenv0.sh

release=$1
update=$2
source=$3
sid_deck_list_file=$4
l1b_config_file=$5

source_dir=$data_directory/$release/$source/level1a

ffs="-"
level=level1b
filebase=$(basename $sid_deck_list_file)
log_dir=$data_directory/$release/$source/$level/log
log_file=$log_dir/${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

exec > $log_file 2>&1

# Get JOB
function nk_jobid {
    output=$($*)
    echo $output | head -n1 | cut -d'<' -f2 | cut -d'>' -f1
}

# These are default and can be overriden by what's set in the configuration file
job_time=01:00
job_memo=3000
# Now loop through the list of sid-dks in the list and
# send subjobs for the monthly files
for p in $(awk '{printf "%s,%s,%s\n",$1,$2,$3}' $sid_deck_list_file)
do
	OFS=$IFS
	IFS=',' read -r -a process <<< "$p"
	IFS=$OFS
	sid_deck=${process[0]}
	inidate=${process[1]}
	enddate=${process[2]}

	sid_deck_log_dir=$log_dir/$sid_deck
	sid_deck_source_dir=$source_dir/$sid_deck

  # Re-initialize scratch directory for deck
  sid_deck_scratch_dir=$scratch_directory/$level/$sid_deck
  echo "Setting deck L1b scratch directory: $sid_deck_scratch_dir"
  rm -rf $sid_deck_scratch_dir;mkdir -p $sid_deck_scratch_dir

	d=$inidate'-01'
	enddate=$enddate'-01'
	counter=1
	while [ "$(date -d "$d" +%Y%m)" -le "$(date -d "$enddate" +%Y%m)" ]
	do
		file_date=$(date -d "$d" +%Y-%m)
		source_filename=$sid_deck_source_dir/'header-'$file_date'-'$release'-'$update'.psv'
		if [ -e $source_filename ]
		then
			echo "$sid_deck, $file_date:: $source_filename listed. BSUB idx: $counter"
      # We need the sid-dck and release to be passed to the l1a_job.sh so that
      # it find the $counter.input file, but we write there the release and update
      # to be able to easily tag the .o and .e files afterwards
			echo ${file_date:0:4} ${file_date:5:8} $release $update $source $sid_deck > $sid_deck_scratch_dir/$counter.input
                        ((counter++))
		else
			echo "$sid_deck, $file_date: NO $source_filename found."
		fi
		d=$(date -I -d "$d + 1 month")
	 done
	 ((counter--))

	 jobid=$(nk_jobid bsub -J $sid_deck'L1Bm'"[1-$counter]" -oo $sid_deck_scratch_dir/"%I.o_main" -eo $sid_deck_scratch_dir/"%I.e_main" -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" $scripts_directory/L1b_merge_job.sh $sid_deck $release $update $source $l1b_config_file)
	 bsub -J L1Bm_ok"[1-$counter]" -w "done($jobid[*])" -oo $sid_deck_scratch_dir/"b%I.oo" -eo $sid_deck_scratch_dir/"b%I.oe" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" $scripts_directory/bsub_array_output_hdlr.sh 0 $sid_deck_scratch_dir 'main' 0 $level
   bsub -J L1Bm_er"[1-$counter]" -w "exit($jobid[*])" -oo $sid_deck_scratch_dir/"b%I.eo" -eo $sid_deck_scratch_dir/"b%I.ee" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" $scripts_directory/bsub_array_output_hdlr.sh 1 $sid_deck_scratch_dir 'main' 0 $level
   jobid_r=$(nk_jobid bsub -J $sid_deck'L1Br'"[1-$counter]" -w "done($jobid)" -oo $sid_deck_scratch_dir/"%I.o_regroup" -eo $sid_deck_scratch_dir/"%I.e_regroup" -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" $scripts_directory/table_regroup_job.sh $sid_deck $release $update $source $level)
   bsub -J L1Br_ok"[1-$counter]" -w "done($jobid_r[*])" -oo $sid_deck_scratch_dir/"b%I.roo" -eo $sid_deck_scratch_dir/"b%I.roe" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" $scripts_directory/bsub_array_output_hdlr.sh 0 $sid_deck_scratch_dir 'regroup' 1 $level
   bsub -J L1Br_er"[1-$counter]" -w "exit($jobid_r[*])" -oo $sid_deck_scratch_dir/"b%I.reo" -eo $sid_deck_scratch_dir/"b%I.ree" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" $scripts_directory/bsub_array_output_hdlr.sh 1 $sid_deck_scratch_dir 'regroup' 1 $level
done
