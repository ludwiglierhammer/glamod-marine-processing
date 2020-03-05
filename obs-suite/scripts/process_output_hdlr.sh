#!/bin/bash
#
# Get job_index and get output and error files from a job that has been
# previously run with that index.
#
# The exit_status is input argument to the script (which has been created to
# be invoqued using job dependency)
# The directory where input, o and e files are is also input
#
# Get from the job_index.input the data identification (date(yyyy mm), release, update)
# and use these to remane the job_index.o|e files:
# - job_index.o: date_release_update.ok if exit status 0
# - job_index.o: date_release_update.error if exit status 1
# - job_index.e: date_release_update.log
#
# Usage: ./process_output_hdlr.sh exit_status sid_deck_scratch_dir $process $level

source ../setpaths.sh

echo 'Vivo'

exit_status=$1
sid_deck_scratch_dir=$2
process=$3
level=$4

job_log_dir=$data_directory/$release/$dsource/$level/log/$sid_dck
file_id=$yr$ffs$mo$ffs$release$ffs$update

ext=ok
if (( exit_status == 1 ));then ext=error;fi

mv $sid_deck_scratch_dir/$process.o $job_log_dir/$file_id$ffs$process.$ext
