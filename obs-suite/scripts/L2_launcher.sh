#!/bin/bash
# Sends a bsub job for every sid-deck listed in a the input file
# to run level2 generation
# - copy level1e to level2
# - create level2 IO plots (after copy)
# - create level2 report (after IO plots)
#
# bsub input, error and output files are located in
# <scratch_dir>/level2/sid_deck and are NOT moved to <data_dir>/level2/log/<sid_deck>
# after job has finished
#
# Main paths are set sourcing r092009_setenv0.sh
#
# sid_deck_list_file is: sid-dck yyyy-mm yyyy-mm
# level2list is a json file initialized by L2_list_create.py and edited to needs,
# per sid-dck info on what to include on level2.
#
# Usage: ./L2_launcher.sh release update source_dataset list_file level2list

# Get JOB
function nk_jobid {
    output=$($*)
    echo $output | head -n1 | cut -d'<' -f2 | cut -d'>' -f1
}


source setenv0.sh

release=$1
update=$2
source=$3
sid_deck_list_file=$4
level2list=$5

ffs="-"
level=level2
filebase=$(basename $sid_deck_list_file)
log_dir=$data_directory/$release/$source/$level/log
log_file=$log_dir/${filebase%.*}$ffs$(date +'%Y%m%d_%H%M').log

exec > $log_file 2>&1

# These are default, maybe should be parameterized to boost job submission when small sid-dcks....
job_time_cp=03:00
job_memo_cp=500
job_time_io=02:00
job_memo_io=10000
job_time_rep=01:00
job_memo_rep=5000
# Now loop through the list of sid-dks in the list and send the jobs
for p in $(awk '{printf "%s,%s,%s\n",$1,$2,$3}' $sid_deck_list_file)
do
	OFS=$IFS
	IFS=',' read -r -a process <<< "$p"
	IFS=$OFS
	sid_deck=${process[0]}
        y_init=${process[1]:0:4}
	y_end=${process[2]:0:4}

	sid_deck_log_dir=$log_dir/$sid_deck
  # Re-initialize scratch directory for deck
  sid_deck_scratch_dir=$scratch_directory/$level/$sid_deck
  echo "Setting deck L1e scratch directory: $sid_deck_scratch_dir"
  rm -rf $sid_deck_scratch_dir;mkdir -p $sid_deck_scratch_dir

  jobid_cp=$(nk_jobid bsub -J $sid_deck'L2c' -oo $sid_deck_scratch_dir/"L2_copy.o" -eo $sid_deck_scratch_dir/"L2_copy.e" -q short-serial -W $job_time_cp -M $job_memo_cp -R "rusage[mem=$job_memo_cp]" python $scripts_directory/L2_main.py $data_directory $sid_deck $release $update $source $level2list)
  jobid_io=$(nk_jobid bsub -J $sid_deck'L2io' -w "done($jobid_cp)" -oo $sid_deck_scratch_dir/"L2_io.e" -eo $sid_deck_scratch_dir/"L2_io.e" -q short-serial -W $job_time_io -M $job_memo_io -R "rusage[mem=$job_memo_io]" python $code_directory/reports/report_io.py $data_directory $release $update $source $level $sid_deck $y_init $y_end)
  bsub -J $sid_deck'L2REP' -w "done($jobid_io)" -oo $sid_deck_scratch_dir/"L2_rep.e" -eo $sid_deck_scratch_dir/"L2_rep.e" -q short-serial -W $job_time_rep -M $job_memo_rep -R "rusage[mem=$job_memo_rep]" python $code_directory/reports/pdf_report_jinja_$level.py $data_directory $release $update $source $sid_deck $y_init $y_end

done
