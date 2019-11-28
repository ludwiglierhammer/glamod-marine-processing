#!/bin/bash
#
# Run a subjob, getting its index from environmental variable LSB_JOBINDEX.
# Find file specific parameters in job_index.input file located in the level1a
# log sid_dck directory of the release.
# Remove pre-exiting products for the same file before processing.
# usage: ./L1a_regroup_job.sh sid_deck release update source

source r092019_setenv0.sh

sid_deck=$1
release=$2
update=$3
dsource=$4
level=$5

level_dir=$data_directory/$release/$dsource/$level/$sid_deck
sid_deck_scratch_dir=$scratch_directory/$level/$sid_deck
quicklooks_dir=$data_directory/$release/$dsource/$level/quicklooks/$sid_deck

job_idx=$LSB_JOBINDEX
yr=$(awk '{print $1}' $sid_deck_scratch_dir/$job_idx.input)
mo=$(awk '{print $2}' $sid_deck_scratch_dir/$job_idx.input)

echo "Launching line:"
echo "python $scripts_directory/table_regroup.py $data_directory $sid_deck $yr $mo $release $update $dsource $level"

python $scripts_directory/table_regroup.py $data_directory $sid_deck $yr $mo $release $update $dsource $level
