#!/bin/bash
# Sends a bsub job for every sid-deck listed in a the input file
# to run the lat-band aggregated time series
#
# Main paths are set with the configuration file run at the beginning (r092009_setenv0.sh)
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./report_ts_launcher.sh release update datasource list_file

source ../scripts/r092019_setenv0.sh

release=$1
update=$2
source=$3
level=$4
sid_deck_list_file=$5

ffs="-"
filebase=$(basename $sid_deck_list_file)
log_dir=$data_directory/$release/$source/$level/reports
log_file=$log_dir/'lat'$ffs'ts'$ffs${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

exec > $log_file 2>&1
# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time=06:00
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
  sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/ts
  echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
  rm -rf $sid_deck_scratch_dir;mkdir -p $sid_deck_scratch_dir
  for param in sst at slp ws wd dpt wbt
	do
	for mode in qcr0-qc0-um all qcr0-qc0 qcr0
	do
			bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_ts_lat_bands.py $data_directory $release $update $source $level $sid_deck $mode $param
    done
  done

done
