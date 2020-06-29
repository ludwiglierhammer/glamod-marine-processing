#!/bin/bash
# This is a program that keeps your address book up to date.


process_level() {
  level_subdirs=$1
  for level_subdir in "${level_subdirs[@]}"
  do
    if [ -d $level_subdir ]
    then
      read -p "Remove directory $level_subdir? [y|n]: " remove
      if [ "$remove" == "y" ]
      then
        echo 'Removing '$level_subdir
        rm -r $level_subdir
      else
        echo 'Will not remove '$level_subdir
      fi
    else
        echo "level subdir $level_subdir not found"
    fi
  done
}

source ../setpaths.sh

release=$1
update=$2
source=$3
sid_dck=$4

source_dir=$data_directory/$release/$source

level=level1a
echo ""
echo "PROCESSING LEVEL $level"
level_dir=$source_dir/$level
declare -a level_subdirs
level_subdirs=($level_dir/$sid_dck $level_dir/quicklooks/$sid_dck $level_dir/log/$sid_dck $level_dir/invalid/$sid_dck $level_dir/excluded/$sid_dck)
process_level "${level_subdirs[@]}"

level=level1b
echo ""
echo "PROCESSING LEVEL $level"
level_dir=$source_dir/$level
declare -a level_subdirs
level_subdirs=($level_dir/$sid_dck $level_dir/quicklooks/$sid_dck $level_dir/log/$sid_dck)
process_level "${level_subdirs[@]}"

level=level1c
echo ""
echo "PROCESSING LEVEL $level"
level_dir=$source_dir/$level
declare -a level_subdirs
level_subdirs=($level_dir/$sid_dck $level_dir/quicklooks/$sid_dck $level_dir/log/$sid_dck $level_dir/invalid/$sid_dck)
process_level "${level_subdirs[@]}"

level=level1d
echo ""
echo "PROCESSING LEVEL $level"
level_dir=$source_dir/$level
declare -a level_subdirs
level_subdirs=($level_dir/$sid_dck $level_dir/quicklooks/$sid_dck $level_dir/log/$sid_dck)
process_level "${level_subdirs[@]}"

level=level1e
echo ""
echo "PROCESSING LEVEL $level"
level_dir=$source_dir/$level
declare -a level_subdirs
level_subdirs=($level_dir/$sid_dck $level_dir/quicklooks/$sid_dck $level_dir/log/$sid_dck)
process_level "${level_subdirs[@]}"

level=level1f
echo ""
echo "PROCESSING LEVEL $level"
level_dir=$source_dir/$level
declare -a level_subdirs
level_subdirs=($level_dir/$sid_dck $level_dir/quicklooks/$sid_dck $level_dir/log/$sid_dck $level_dir/reports/$sid_dck)
process_level "${level_subdirs[@]}"

level=level2
echo ""
echo "PROCESSING LEVEL $level"
level_dir=$source_dir/$level
declare -a level_subdirs
level_subdirs=($level_dir/$sid_dck $level_dir/quicklooks/$sid_dck $level_dir/excluded/$sid_dck $level_dir/log/$sid_dck $level_dir/reports/$sid_dck)
process_level "${level_subdirs[@]}"
