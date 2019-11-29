#!/bin/bash
#
# Run a subjob, getting its index from environmental variable LSB_JOBINDEX.
# Find file specific parameters in job_index.input file located in the
# <scratch_dir>/level1e/sid_deck
#
# Remove pre-exiting products for the same file-id before processing.
#
# usage: ./L1e_main_job.sh sid_deck release update source


source setenv0.sh

sid_deck=$1
release=$2
update=$3
source=$4
level=level1e
level_dir=$data_directory/$release/$source/$level/$sid_deck
sid_deck_scratch_dir=$scratch_directory/$level/$sid_deck
log_dir=$data_directory/$release/$source/$level/log/$sid_deck
outlooks_dir=$data_directory/$release/$source/$level/quicklooks/$sid_deck

job_idx=$LSB_JOBINDEX
yr=$(awk '{print $1}' $sid_deck_scratch_dir/$job_idx.input)
mo=$(awk '{print $2}' $sid_deck_scratch_dir/$job_idx.input)
ffs="-"

echo "Removing release $release update $update $source $sid_deck $yr-$mo products and job outputs"
file_id=$yr$ffs$mo$ffs$release$ffs$update
rm $log_dir/$file_id*.* 2>/dev/null
rm $outlooks_dir/$file_id.* 2>/dev/null
rm $level_dir/*$ffs$file_id.* 2>/dev/null

echo "Launching line:"
echo "python $scripts_directory/L1e_main.py $data_directory $sid_deck $yr $mo $release $update $source"

python $scripts_directory/L1e_main.py $data_directory $sid_deck $yr $mo $release $update $source
