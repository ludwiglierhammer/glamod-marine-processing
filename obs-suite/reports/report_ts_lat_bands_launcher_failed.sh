#!/bin/bash
# Sends a bsub job for every sid-deck listed in a the input file
# to run the lat-band aggregated time series
#
# Main paths are set with the configuration file run at the beginning (r092009_setenv0.sh)
#
# Usage: ./report_ts_launcher.sh release update datasource

source ../scripts/setenv0.sh

release=$1
update=$2
source=$3
level=$4

ffs="-"
filebase='persistent_failures'
log_dir=$data_directory/$release/$source/$level/reports
log_file=$log_dir/'lat'$ffs'ts'$ffs${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

exec > $log_file 2>&1
# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time=06:00
job_memo=4000
# Now loop through the list of sid-dks in the list, find its l1a config and
# send jobs for the monthly files
# param=[sst at slp ws wd dpt wbt]
# mode=[qcr0-qc0-um all qcr0-qc0 qcr0]

sid_deck=140-117
sid_deck_log_dir=$log_dir/$sid_deck
if [ ! -d $sid_deck_log_dir ]
then
  mkdir -p $sid_deck_log_dir
fi
# Re-initialize scratch directory for deck
sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/ts
echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
param=ws
mode=qcr0-qc0
bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_ts_lat_bands.py $data_directory $release $update $source $level $sid_deck $mode $param

sid_deck=090-209
sid_deck_log_dir=$log_dir/$sid_deck
if [ ! -d $sid_deck_log_dir ]
then
  mkdir -p $sid_deck_log_dir
fi
# Re-initialize scratch directory for deck
sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/ts
echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
param=wbt
mode=all
bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_ts_lat_bands.py $data_directory $release $update $source $level $sid_deck $mode $param

sid_deck=090-229
sid_deck_log_dir=$log_dir/$sid_deck
if [ ! -d $sid_deck_log_dir ]
then
  mkdir -p $sid_deck_log_dir
fi
# Re-initialize scratch directory for deck
sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/ts
echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
param=slp
mode=qcr0-qc0
bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_ts_lat_bands.py $data_directory $release $update $source $level $sid_deck $mode $param

sid_deck=103-792
sid_deck_log_dir=$log_dir/$sid_deck
if [ ! -d $sid_deck_log_dir ]
then
  mkdir -p $sid_deck_log_dir
fi
# Re-initialize scratch directory for deck
sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/ts
echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
param=sst
mode=qcr0
bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_ts_lat_bands.py $data_directory $release $update $source $level $sid_deck $mode $param


sid_deck=079-888
sid_deck_log_dir=$log_dir/$sid_deck
if [ ! -d $sid_deck_log_dir ]
then
  mkdir -p $sid_deck_log_dir
fi
# Re-initialize scratch directory for deck
sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/ts
echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
param=slp
mode=qcr0-qc0
bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_ts_lat_bands.py $data_directory $release $update $source $level $sid_deck $mode $param

sid_deck=112-926
sid_deck_log_dir=$log_dir/$sid_deck
if [ ! -d $sid_deck_log_dir ]
then
  mkdir -p $sid_deck_log_dir
fi
# Re-initialize scratch directory for deck
sid_deck_scratch_dir=$scratch_directory/$level/reports/$sid_deck/ts
echo "Setting deck reports scratch directory: $sid_deck_scratch_dir"
param=wbt
mode=all
bsub -J $sid_deck$mode$param'TS' -oo $sid_deck_scratch_dir/$mode$param'.o' -eo $sid_deck_scratch_dir/$mode$param'.e' -q short-serial -W $job_time -M $job_memo -R "rusage[mem=$job_memo]" python $code_directory/reports/report_ts_lat_bands.py $data_directory $release $update $source $level $sid_deck $mode $param
