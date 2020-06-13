#!/bin/bash

#. FUNCTIONS -------------------------------------------------------------------
# Get JOB
function nk_jobid {
    output=$($*)
    echo $output | head -n1 | cut -d'<' -f2 | cut -d'>' -f1
}
# ------------------------------------------------------------------------------
source ../setpaths.sh
source ../setenv2.sh

# Here make sure we are using fully expanded paths, as some may be passed to a config file
log_dir=$1
script_config_file=$2

pyscript=$um_code_directory/data_summaries/monthly_grids_ts_global_params.py

job_time_hhmm=15:00
job_memo_mbi=5000
for table in header observations-sst observations-at observations-dpt observations-wd observations-ws observations-slp
do

   jobid=$(nk_jobid bsub -J $table -oo $log_dir/$table"_grid_ts.log" -eo $log_dir/$table"_grid_ts.log" -q short-serial -W $job_time_hhmm -M $job_memo_mbi -R "rusage[mem=$job_memo_mbi]" python $pyscript $table $script_config_file )
done
