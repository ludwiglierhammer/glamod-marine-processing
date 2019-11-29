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
# Usage: ./bsub_array_output_hdlr.sh exit_status sid_deck_scratch_dir suffix_loggers rm_input_files
source setenv0.sh

exit_status=$1
sid_deck_scratch_dir=$2
suffix_loggers=$3
rm_input=$4
level=$5
job_idx=$LSB_JOBINDEX

job_input=$sid_deck_scratch_dir/$job_idx.input
parser_error="Error parsing $job_input file.File not found"

if [ ! -s $job_input ];then echo $parser_error $sid_deck_scratch_dir/$job_idx.parser;fi

ffs="-"
yr=$(awk '{print $1}' $job_input)
mo=$(awk '{print $2}' $job_input)
release=$(awk '{print $3}' $job_input)
update=$(awk '{print $4}' $job_input)
dsource=$(awk '{print $5}' $job_input)
sid_dck=$(awk '{print $6}' $job_input)


job_log_dir=$data_directory/$release/$dsource/$level/log/$sid_dck
file_id=$yr$ffs$mo$ffs$release$ffs$update

ext=ok
if (( exit_status == 1 ));then ext=error;fi

mv $sid_deck_scratch_dir/$job_idx.o_$suffix_loggers $job_log_dir/$file_id$ffs$suffix_loggers.$ext
mv $sid_deck_scratch_dir/$job_idx.e_$suffix_loggers $job_log_dir/$file_id$ffs$suffix_loggers.log
# Consider removing *.input files when this is working....
if (( rm_input == 1 ));then rm $sid_deck_scratch_dir/$job_idx.input;fi
