#!/bin/bash
# Sends a bsub job for every sid-deck listed in a the input file
# to run level2 generation
# - copy level1e to level2
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
#
# Usage: ./level2.sh release update source_dataset list_file level2_file

source ../setpaths.sh
source ../setenv0.sh

release=$1
update=$2
source=$3
l2_file=$4
sid_deck_list_file=$5

ffs="-"
level=level2
filebase=$(basename $sid_deck_list_file)
log_dir=$data_directory/$release/$source/$level/log
log_file=$log_dir/${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

exec > $log_file 2>&1

# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time_cp=10:00
job_memo_cp=500

# Now loop through the list of sid-dks in the list and send the jobs
for sid_deck in $(awk '{print $1}' $sid_deck_list_file)
do
	sid_deck_log_dir=$log_dir/$sid_deck
  bsub -J $sid_deck'L2c' -oo $sid_deck_log_dir/"level2.o" -eo $sid_deck_log_dir/"level2.o" -q short-serial -W $job_time_cp -M $job_memo_cp -R "rusage[mem=$job_memo_cp]" python $scripts_directory/level2.py $data_directory $release $update $source $sid_deck $l2_file
done
