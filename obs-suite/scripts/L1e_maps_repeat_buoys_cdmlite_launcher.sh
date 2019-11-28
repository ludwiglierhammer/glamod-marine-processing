#!/bin/bash
# Sends a bsub array of jobs for every sid-deck listed in a the input file
# to run the L1d level
# Main paths are set with the configuration file run at the beginning (r092009_setenv0.sh)
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./L1e_maps_repeat_launcher.sh release update datasource list_file


# Get JOB
function nk_jobid {
    output=$($*)
    echo $output | head -n1 | cut -d'<' -f2 | cut -d'>' -f1
}


source r092019_setenv0.sh

release=$1
update=$2
source=$3
sid_deck_list_file=$4

ffs="-"
source_level=level1e
level=level1e
filebase=$(basename $sid_deck_list_file)
log_dir=$data_directory/$release/$source/$level/log
log_file=$log_dir/${filebase%.*}$ffs$(date +'%Y%m%d_%H%M')_maps.log

exec > $log_file 2>&1

source_dir=$data_directory/$release/$source/$source_level
# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time=03:00
job_memo=4000
# Now loop through the list of sid-dks in the list, find its l1a config and
# send jobs for the monthly files
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
  echo "Setting deck L1c scratch directory: $sid_deck_scratch_dir"
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
      # We need the sid-dck and release to be passed to the l1c_job.sh so that
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

	 jobid=$(nk_jobid bsub -J $sid_deck'L1Em'"[1-$counter]" -oo $sid_deck_scratch_dir/"%I.o_map" -eo $sid_deck_scratch_dir/"%I.e_map" -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" $scripts_directory/L1e_maps_repeat_buoys_cdmlite_job.sh $sid_deck $release $update $source)
	 bsub -J L1Em_ok"[1-$counter]" -w "done($jobid[*])" -oo $sid_deck_scratch_dir/"b%I.oo" -eo $sid_deck_scratch_dir/"b%I.oe" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" $scripts_directory/bsub_array_output_hdlr.sh 0 $sid_deck_scratch_dir 'map' 0 $level
   bsub -J L1Em_er"[1-$counter]" -w "exit($jobid[*])" -oo $sid_deck_scratch_dir/"b%I.eo" -eo $sid_deck_scratch_dir/"b%I.ee" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" $scripts_directory/bsub_array_output_hdlr.sh 1 $sid_deck_scratch_dir 'map' 0 $level
done
