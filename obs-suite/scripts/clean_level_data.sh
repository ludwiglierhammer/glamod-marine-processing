#!/bin/bash
#
# Remove all files from the data section of a processing level
#
# usage: ./clean_level_data.sh sid_deck release update source level

source r092019_setenv0.sh

sid_deck=$1
release=$2
update=$3
source=$4
level=$5
ffs='-'

if [ $# -lt 5 ]
  then
    echo "Input arguments missing. Usage: clean_level_data.sh sid-dck release update source level"
		exit 1
fi

ddata=$data_directory/$release/$source/$level/$sid_deck
dlog=$data_directory/$release/$source/$level/log/$sid_deck
log_file=$dlog/cleaning$ffs$(date +'%Y%m%d_%H%M').log

if [ ! -d $ddata ]
then
	echo Cannot find data directory $ddata
  exit 1
fi

if [ ! -d $dlog ]
then
	echo Cannot find log directory $dlog
  exit 1
fi

exec > $log_file 2>&1

echo Following files will be removed from $ddata:
ls $ddata
rm $ddata/*

echo 'Done'
