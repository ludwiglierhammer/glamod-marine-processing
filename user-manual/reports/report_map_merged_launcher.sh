#!/bin/bash
# Sends the corresponding bsub jobs for every sid-deck listed in a the input file
# to create summary maps on the CDM data in the input level and its corresponding png images
#
# The summary maps are performed on the following report_quality - param quality_flag combinations:
# all: all data in level
# qcr0-qc0: only report_quality and param quality_flag passed
#
# Main paths are set with the configuration file run at the beginning (setenv1.sh)
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./report_map_merged_launcher.sh release update datasource list_file

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
job_time=04:00
job_memo=20000
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

  # Send maps for all data: nc files
  sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/map_merge/all
  echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
  rm -rf $sid_deck_scratch_dir;mkdir -p $sid_deck_scratch_dir
  for table in header observations-sst observations-slp observations-at observations-wd observations-ws observations-wbt observations-dpt
  do
	   bsub -J $sid_deck$table'allM' -oo $sid_deck_scratch_dir/$table'M.o' -eo $sid_deck_scratch_dir/$table'M.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_map_merged.py $data_directory $release $update $source $level $sid_deck $table all all $sid_deck_scratch_dir/$table
  done


  # Send maps for best qc combination data: nc files
  sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/map_merge/qcr0-qc0
  echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
  rm -rf $sid_deck_scratch_dir;mkdir -p $sid_deck_scratch_dir
  for table in header observations-sst observations-slp observations-at observations-wd observations-ws observations-wbt observations-dpt
  do
	   bsub -J $sid_deck$table'bestM' -oo $sid_deck_scratch_dir/$table'M.o' -eo $sid_deck_scratch_dir/$table'M.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_map_merged.py $data_directory $release $update $source $level $sid_deck $table 0 0 $sid_deck_scratch_dir/$table
  done
done
