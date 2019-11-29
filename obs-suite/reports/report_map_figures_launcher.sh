#!/bin/bash
# Sends a the corresponding bsub jobs for every sid-deck listed in a the input file
# to create summary maps on the CDM data in the input level and its corresponding png images
#
# The summary maps are performed on the following report_quality - param quality_flag combinations:
# all: all data in level
# qcr0-qc0: only report_quality and param quality_flag passed
#
# Main paths are set with the configuration file run at the beginning (r092009_setenv0.sh)
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./report_maps_launcher.sh release update datasource list_file

source ../scripts/setenv1.sh

# Get JOB
function nk_jobid {
    output=$($*)
    echo $output | head -n1 | cut -d'<' -f2 | cut -d'>' -f1
}

release=$1
update=$2
source=$3
level=$4
sid_deck_list_file=$5

ffs="-"
filebase=$(basename $sid_deck_list_file)
log_dir=$data_directory/$release/$source/$level/reports
log_file=$log_dir/maps$ffs${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

exec > $log_file 2>&1
# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time=01:00
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

  # Send maps for all data: png figures
  sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/map_merge/all
  echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
  ext=all
  bsub -J $sid_deck$ext'P' -oo $sid_deck_scratch_dir/$ext'P.o' -eo $sid_deck_scratch_dir/$ext'P.e' -q short-serial -W 00:30 -M 1000 -R "rusage[mem=1000]" python $code_directory/reports/report_map_figures.py $data_directory $release $update $source $level $sid_deck $ext

  # Send maps for best qc combination data: png figures
  sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/map_merge/qcr0-qc0
  echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
  for ext in qcr0-qc0-um qcr0-qc0
	do
		bsub -J $sid_deck$ext'P' -oo $sid_deck_scratch_dir/$ext'P.o' -eo $sid_deck_scratch_dir/$ext'P.e' -q short-serial -W 00:30 -M 1000 -R "rusage[mem=1000]" python $code_directory/reports/report_map_figures.py $data_directory $release $update $source $level $sid_deck $ext
  done
done
