#!/bin/bash
#
# Run a subjob, getting its index from environmental variable LSB_JOBINDEX.
# Find file specific parameters in job_index.input file located in the level1a
# log sid_dck directory of the release.
# Remove pre-exiting products for the same file before processing.
# usage: ./L1a_regroup_job.sh sid_deck release update source

source r092019_setenv0.sh

config_file=$code_directory/configuration_files/r092019_000000_list.txt
to_remove_file=$code_directory/configuration_files/r092019_000000_level1a_remove.txt
ddata=$data_directory/r092019/ICOADS_R3.0.0T/level1a
dlog=$data_directory/r092019/ICOADS_R3.0.0T/level1a/log
dql=$data_directory/r092019/ICOADS_R3.0.0T/level1a/quicklooks


for p in $(awk '{printf "%s,%s,%s\n",$1,substr($2,1,4),substr($3,1,4)}' $config_file)
do
	OFS=$IFS
	IFS=',' read -r -a process <<< "$p"
	IFS=$OFS
	sid_deck=${process[0]}
	iniyr=${process[1]}
	endyr=${process[2]}
  echo $sid_deck

  ls $ddata/$sid_deck/*.psv | awk -v yeari==$iniyr -v yeare==$endyr 'substr($1,length($0)-25,4)<yeari && substr($1,length($0)-25,4)>yeare {print $0}' >> $to_remove_file
  ls $dlog/$sid_deck/*.* | awk -F"/" -v yeari==$iniyr -v yeare==$endyr 'substr($NF,1,4)<yeari && substr($NF,1,4)>yeare {print $0}' >> $to_remove_file
  ls $dql/$sid_deck/*.json | awk -F"/" -v yeari==$iniyr -v yeare==$endyr 'substr($NF,1,4)<yeari && substr($NF,1,4)>yeare {print $0}' >> $to_remove_file
  ls $dql/$sid_deck/*.nc | awk -v yeari==$iniyr -v yeare==$endyr 'substr($1,length($0)-25,4)<yeari && substr($1,length($0)-25,4)>yeare {print $0}' >> $to_remove_file

done
