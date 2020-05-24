#!/bin/bash
# Sends a bsub job for every sid-deck listed in a the input file
# to run the pdf report generation
# Main paths are set with the configuration file run at the beginning (r092009_setenv0.sh)
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./pdf_report_jinja_launcher.sh release update datasource level list_file

source ../scripts/setenv0.sh

release=$1
update=$2
source=$3
level=$4
periods_file=$5
sid_deck_list_file=$6

user_manual_dir=$data_directory/user-manual/release_summaries

ffs="-"
filebase=$(basename $sid_deck_list_file)
log_dir=$user_manual_dir/$release/$source/log
log_file=$log_dir/pdf$ffs${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

echo $log_file

exec > $log_file 2>&1
# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time=00:20
job_memo=4000
# Now loop through the list of sid-dks in the list, find its l1a config and
# send jobs for the monthly files
for p in $(awk '{printf "%s,%s,%s\n",$1,$2,$3}' $sid_deck_list_file)
do
	OFS=$IFS
	IFS=',' read -r -a process <<< "$p"
	IFS=$OFS
	sid_deck=${process[0]}
	y_init=${process[1]:0:4}
	y_end=${process[2]:0:4}

	sid_deck_log_dir=$log_dir/$sid_deck


  if [ ! -d $sid_deck_log_dir ]
  then
    mkdir -p $sid_deck_log_dir
  fi

  # Re-initialize scratch directory for deck
  sid_deck_scratch_dir=$scratch_directory/reports/$sid_deck
  echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
  rm -rf $sid_deck_scratch_dir;mkdir -p $sid_deck_scratch_dir

	bsub -J $sid_deck'REP' -oo $sid_deck_scratch_dir/'REP.o' -eo $sid_deck_scratch_dir/'REP.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $um_code_directory/reports/pdf_report_jinja_$level.py $user_manual_dir $release $update $source $sid_deck $periods_file
done
