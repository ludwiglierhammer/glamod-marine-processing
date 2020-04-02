#!/bin/bash
# Sends a bsub array of jobs for every sid-deck listed in a the input file
# to run the corresponding script
#
# Within the sid-deck array, a subjob is only submitted if the corresponding
# source monthly file is available.
#
# bsub input, error and output files are initially located in
# <scratch_dir>/level1a/sid_dck
#
# Main paths are set sourcing r092009_setenv0.sh
#
# process_list is: sid-dck
#
# Usage: ./process_array_launcher.sh process_config_file sid_dck_periods_file list_file -f 0|1 -r 0|1 -s yyyy -e yyyy
# Optional kwargs:
# -f: process only failed (0) | process all (1 or none)
# -r: remove source level data (0) | do not remove source level data (1 or none)
# -s: start processing year (defaults to sid-dck initial year)
# -e: end processing year (defaults to sid-dck last year)

#. FUNCTIONS -------------------------------------------------------------------
# Write entry to json input file
function to_json {
    printf "\"%s\":\"%s\",\n" $2 $3 >> $1
}

# Get JOB
function nk_jobid {
    output=$($*)
    echo $output | head -n1 | cut -d'<' -f2 | cut -d'>' -f1
}
# Check var exists
function check_config {
    if [ -z $2 ]
    then
      echo "ERROR: CONFIGURATION VARIABLE $1 is empty"
      return 1
    else
      echo "CONFIGURATION VARIABLE $1 set to $2"
      return 0
    fi
}
# Check var exists, otherwise default
function check_soft {
    if [ -z $2 ]
    then
      echo "WARNING: CONFIGURATION VARIABLE $1 is empty, will use default"
      return 1
    else
      echo "CONFIGURATION VARIABLE $1 set to $2"
      return 0
    fi
}
# Check dir exists
function check_dir {
    if [ -d $2 ]
    then
      echo "DIRECTORY $1 set to $2"
      return 0
    else
      echo "ERROR: DIRECTORY $1 NOT FOUND: $2"
      return 1
    fi
}
# Check file exists
function check_file {
    if [ -s $2 ]
    then
      echo "FILE $1 is $2"
      return 0
    else
      echo "ERROR: can't find or zero size $1 FILE: $2"
      return 1
    fi
}
#. END FUNCTIONS ---------------------------------------------------------------

#. PARAMS ----------------------------------------------------------------------
FFS="-"
#. END PARAMS ------------------------------------------------------------------

#. INARGS ----------------------------------------------------------------------
# Here make sure we are using fully expanded paths, as some may be passed to a config file
process_config_file=$(readlink --canonicalize  $1)
sid_dck_periods_file=$(readlink --canonicalize  $2)
process_list=$(readlink --canonicalize $3)

shift 3

while getopts ":f:r:s:e:" opt; do
  case $opt in
    f) failed="$OPTARG"
    ;;
    r) remove="$OPTARG"
    ;;
    s) process_start="$OPTARG"
    ;;
    e) process_end="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done
if [ "$failed" == '0' ];then failed_only=true;else failed_only=false;fi
if [ "$remove" == '0' ];then remove_source_level=true;else remove_source_level=false;fi
if [ -z "$process_start" ];then process_start=-99999;fi
if [ -z "$process_end" ];then process_end=99999;fi
#. CONFIG FILES & ENVIRONMENT --------------------------------------------------
source ../setpaths.sh

check_file process_config_file $process_config_file || exit 1
check_file sid_dck_periods_file $sid_dck_periods_file || exit 1


process=$(basename $process_config_file ".json")
env=$(jq -r '.["job_config"].environment | select (.!=null)' $process_config_file)
source ../setenv$env.sh
echo
#. END INARGS, CONFIG FILES AND ENVIRONMENT ------------------------------------

#. GET MAIN CONFIG -------------------------------------------------------------
release=$(jq -r '.release | select (.!=null)' $process_config_file)
update=$(jq -r '.update | select (.!=null)' $process_config_file)
dataset=$(jq -r '.dataset | select (.!=null)' $process_config_file)
data_level=$(jq -r '.["job_config"].data_level | select (.!=null)' $process_config_file)
source_level=$(jq -r '.["job_config"].source_level | select (.!=null)' $process_config_file)
source_file_ext=$(jq -r '.["job_config"].source_file_ext | select (.!=null)' $process_config_file)
source_filename_prefix=$(jq -r '.["job_config"].source_filename_prefix | select (.!=null)' $process_config_file)
source_filename_suffix=$(jq -r '.["job_config"].source_filename_suffix | select (.!=null)' $process_config_file)
job_time_hr=$(jq -r '.["job_config"].job_time_hr | select (.!=null)' $process_config_file)
job_time_min=$(jq -r '.["job_config"].job_time_min | select (.!=null)' $process_config_file)
job_memo_mb=$(jq -r '.["job_config"].job_memo_mb | select (.!=null)' $process_config_file)
script_name=$(jq -r '.["job_config"].script_name | select (.!=null)' $process_config_file)
for confi in release update dataset data_level source_level source_file_ext job_time_hr job_time_min job_memo_mb
do
  check_config $confi "${!confi}"  || exit 1
done
#. END GET MAIN CONFIG ---------------------------------------------------------

# MAIN DIRS, LOG AND CONFIRM ---------------------------------------------------
if [ $source_level == "level0" ]
then
  source_dir=$data_directory/datasets/$dataset/level0
  if $remove_source_level
  then
    remove_source_level=false
    echo
    echo "WARNING!!!: USER REQUESTED REMOVE SOURCE LEVEL DISABLED FOR SOURCE LEVEL0"
    echo
  fi
else
  source_dir=$data_directory/$release/$dataset/$source_level
fi

if [ "$data_level" == "$source_level" ] && $remove_source_level
then
  remove_source_level=false
  echo
  echo "WARNING!!!: USER REQUESTED REMOVE SOURCE LEVEL DISABLED FOR SOURCE LEVEL SAME AS DATA LEVEL"
  echo
fi

data_dir=$data_directory/$release/$dataset/$data_level
log_dir=$data_dir/log

for diri in source_dir data_dir log_dir
do
  check_dir $diri "${!diri}" || exit 1
done

for confi in failed_only remove_source_level process_start process_end
do
  check_config $confi "${!confi}"  || exit 1
done

echo
read -p "Do you want to continue (Y/y/N/n)? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1 # handle exits from shell or function but don't exit interactive shell
fi

filebase=$(basename $process_list)
log_file=$log_dir/$process$FFS${filebase%.*}$FFS$(date +'%Y%m%d_%H%M').log

echo "LOGGING TO $log_file"

exec > $log_file 2>&1
# END MAIN DIRS, LOG AND CONFIRM -----------------------------------------------

job_time_hhmm=$job_time_hr":"$job_time_min

# PROCESS ALL SID-DCKS FROM LIST -----------------------------------------------
for sid_dck in $(awk '{print $1}' $process_list)
do
  echo
  echo "---------------------------"
  echo "INFO: processing $sid_dck"
  echo "---------------------------"
  job_memo_mbi=$job_memo_mb
  job_time_hri=$job_time_hr
  job_time_mini=$job_time_min
  # Get processing period
  year_init=$(jq -r --arg sid_dck "$sid_dck" '.[$sid_dck] | .year_init | select (.!=null)' $sid_dck_periods_file)
  year_end=$(jq -r --arg sid_dck "$sid_dck" '.[$sid_dck] | .year_end | select (.!=null)' $sid_dck_periods_file)
  check_config year_init $year_init || exit 1
  check_config year_end $year_end || exit 1
  if (( process_start > year_init ));then year_init=$process_start;fi
  if (( process_end < year_end ));then year_end=$process_end;fi
  # Set source-deck specific job settings and directories
	job_memo_mb_=$(jq -r --arg sid_dck "$sid_dck" '.["job_config"] | .[$sid_dck].job_memo_mb | select (.!=null)' $process_config_file)
  job_time_hr_=$(jq -r --arg sid_dck "$sid_dck" '.["job_config"] | .[$sid_dck].job_time_hr | select (.!=null)' $process_config_file)
	job_time_min_=$(jq -r --arg sid_dck "$sid_dck" '.["job_config"] | .[$sid_dck].job_time_min | select (.!=null)' $process_config_file)

  check_soft job_memo_mb_ $job_memo_mb_ && job_memo_mbi=$job_memo_mb_
  check_soft job_time_hr_ $job_time_hr_ && job_time_hri=$job_time_hr_
  check_soft job_time_min_ $job_time_min_ && job_time_mini=$job_time_min_
  job_time_hhmm=$job_time_hri":"$job_time_mini

	sid_dck_log_dir=$log_dir/$sid_dck
	sid_dck_source_dir=$source_dir/$sid_dck

  sid_dck_scratch_dir=$scratch_directory/$release/$dataset/$process/$sid_dck
  echo "INFO: Setting deck $process scratch directory: $sid_dck_scratch_dir"
  rm -rf $sid_dck_scratch_dir;mkdir -p $sid_dck_scratch_dir

  # Loop throuhg period and send subjob only if source level file is available
	d=$year_init'-01-01'
	enddate=$year_end'-12-01'
	counter=1
	while [ "$(date -d "$d" +%Y%m)" -le "$(date -d "$enddate" +%Y%m)" ]
	do
		file_date=$(date -d "$d" +%Y-%m)
    yyyy=${file_date:0:4}
    mm=${file_date:5:8}
		source_filename=$sid_dck_source_dir/$source_filename_prefix"*"$file_date"*"$source_filename_suffix.$source_file_ext
    log_basenamei=$yyyy$FFS$mm$FFS$release$FFS$update
    test -e $sid_dck_log_dir/$log_basenamei.failed
    failed=$?
    if [ "$failed" == 0 ];then failed=true;else failed=false;fi
    if [ 0 -lt $(ls $source_filename 2>/dev/null | wc -w) ]
		then
      if $failed_only && ! $failed
      then
        echo "INFO: FAILED ONLY MODE. $sid_dck, $file_date: already processed successfully. Not listed"
      else
        rm $sid_dck_log_dir/$log_basenamei.*
  			echo "INFO: $sid_dck, $file_date: $source_filename listed. BSUB idx: $counter"
        cp $process_config_file $sid_dck_scratch_dir/$counter.input
        python config_array.py $sid_dck_scratch_dir/$counter.input $data_directory $sid_dck $yyyy $mm
        ((counter++))
      fi
		else
			echo "WARNING: $sid_dck, $file_date: NO $source_filename found."
		fi
		d=$(date -I -d "$d + 1 month")
	 done
	 ((counter--))
   jobid=$(nk_jobid bsub -J $sid_dck$process"[1-$counter]" -oo $sid_dck_scratch_dir/"%I.o" -eo $sid_dck_scratch_dir/"%I.o" -q short-serial -W $job_time_hhmm -M $job_memo_mbi -R "rusage[mem=$job_memo_mbi]" \
   python $scripts_directory/$script_name $sid_dck_scratch_dir/\$LSB_JOBINDEX.input)
   #
   # jobid=$(nk_jobid bsub -J $sid_dck$process"[1-$counter]" -oo $sid_dck_scratch_dir/"%I.o" -eo $sid_dck_scratch_dir/"%I.o" -q short-serial -W $job_time_hhmm -M $job_memo_mbi -R "rusage[mem=$job_memo_mbi]" \
   # python $scripts_directory/process_array.py $scratch_directory $data_directory $release $update $dataset $process $data_level $sid_dck $process_config_file)
   #
   # bsub -J OK"[1-$counter]" -w "done($jobid[*])" -oo $sid_dck_scratch_dir/"%I.ho" -eo $sid_dck_scratch_dir/"%I.ho" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" \
   # python $scripts_directory/process_array_output_hdlr.py $scratch_directory $data_directory $release $update $dataset $process $data_level $sid_dck 0 1
   #
   # bsub -J ER"[1-$counter]" -w "exit($jobid[*])" -oo $sid_dck_scratch_dir/"%I.ho" -eo $sid_dck_scratch_dir/"%I.ho" -q short-serial -W 00:01 -M 10 -R "rusage[mem=10]" \
   # python $scripts_directory/process_array_output_hdlr.py $scratch_directory $data_directory $release $update $dataset $process $data_level $sid_dck 1 1
   #
   # if $remove_source_level
   # then
   #   echo 'Process source level data ('$source_level') removal requested'
   #   jobid_c=$(nk_jobid bsub -J $sid_dck'remove' -w "done($jobid)" -oo $sid_dck_scratch_dir/"remove.co" -eo $sid_dck_scratch_dir/"remove.co" -q short-serial -W 00:15 -M 100 -R "rusage[mem=100]" $scripts_directory/remove_level_data.sh $sid_dck $release $update $dataset $source_level)
   # else
   #   echo 'Process source level data ('$source_level') removal not requested'
   # fi

done
# END PROCESS ALL SID-DCKS FROM LIST -------------------------------------------
