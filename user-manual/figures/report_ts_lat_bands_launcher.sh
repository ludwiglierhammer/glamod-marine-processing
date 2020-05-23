#!/bin/bash
# Sends a bsub job for every sid-deck listed in a the input file
# to run the lat-band aggregated time series
#
# Main paths are set with the configuration file run at the beginning (r092009_setenv0.sh)
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./report_ts_launcher.sh release dataset outdir list_file

source ../setpaths.sh
source ../setenv0.sh

release=$1
dataset=$2
outdir=$(readlink --canonicalize $3)
sid_deck_list_file=$(readlink --canonicalize $4)

ffs="-"
filebase=$(basename $sid_deck_list_file)
log_dir=$outdir
log_file=$log_dir/'lat'$ffs'ts'$ffs${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

exec > $log_file 2>&1
# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time=06:00
job_memo=4000
# Now loop through the list of sid-dks in the list, find its l1a config and
# send jobs for the monthly files
for sid_deck in $(awk '{print $1}' $sid_deck_list_file)
do

	sid_deck_log_dir=$log_dir/$sid_deck
  if [ ! -d $sid_deck_log_dir ]
  then
    mkdir -p $sid_deck_log_dir
  fi

  # Re-initialize scratch directory for deck
  sid_deck_scratch_dir=$scratch_directory/obs_lat_ts/$sid_deck
  echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
  rm -rf $sid_deck_scratch_dir;mkdir -p $sid_deck_scratch_dir
  for param in sst at slp ws wd dpt wbt
      do
        for mode in all optimal
	do
	bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.o' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $um_code_directory/figures/report_ts_lat_bands.py $data_directory/user_manual/release_summaries $release $dataset $sid_deck $mode $param $outdir/$sid_deck
        done
     done
done
