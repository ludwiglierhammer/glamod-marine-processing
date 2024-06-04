#!/bin/bash
#
# Remove all files from the data section of a processing level
#
# This does NOT support removal of level0 data which lays in a different
# directory structure than the release data and should not be removed!
#
# usage: ./remove_level_data.sh sid_deck release update source level

source ../setpaths.sh

sid_deck=$1
release=$2
update=$3
source=$4
level=$5
ffs='-'

if [ $# -lt 5 ]
  then
    echo "ERROR: Input arguments missing. Usage: $0 sid-dck release update source level"
		exit 1
fi

if [ "$level" == 'level0' ]
then
  echo "ERROR: level0 data removal is not supported by this script"
  exit 1
fi

ddata=$data_directory/$release/$source/$level/$sid_deck
dlog=$data_directory/$release/$source/$level/log/$sid_deck
log_file=$dlog/cleaning$ffs$(date +'%Y%m%d_%H%M').log

if [ ! -d $ddata ]
then
	echo "ERROR: Cannot find data directory $ddata"
  exit 1
fi

if [ ! -d $dlog ]
then
	echo "ERROR: Cannot find log directory $dlog"
  exit 1
fi

exec > $log_file 2>&1

echo Following files will be removed from $ddata:
ls $ddata
rm $ddata/*

echo 'Done'
