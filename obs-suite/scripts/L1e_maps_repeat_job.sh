#!/bin/bash
#
# QC directory is in setenv0.sh as it was not included in the release directory tree
#
# Run a subjob, getting its index from environmental variable LSB_JOBINDEX.
# Find file specific parameters in job_index.input file located in the
# l1e/sid_dck directory in scratch
# Remove pre-exiting products for the same file before processing.
# usage: ./L1e_maps_repeat_job.sh sid_deck release update source

source setenv0.sh

sid_deck=$1
release=$2
update=$3
source=$4
level=level1e
sid_deck_scratch_dir=$scratch_directory/$level/$sid_deck

job_idx=$LSB_JOBINDEX
yr=$(awk '{print $1}' $sid_deck_scratch_dir/$job_idx.input)
mo=$(awk '{print $2}' $sid_deck_scratch_dir/$job_idx.input)
ffs="-"

echo "Launching line:"
echo "python $scripts_directory/L1e_maps_repeat.py $data_directory $sid_deck $yr $mo $release $update $source"

python $scripts_directory/L1e_maps_repeat.py $data_directory $sid_deck $yr $mo $release $update $source
