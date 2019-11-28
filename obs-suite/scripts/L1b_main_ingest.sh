#!/bin/bash
#
# Script to reformat the original output from the linkage/duplicate processing/analysis
#
# This is tailored to the output of this process as of Autumn2019 (C3S Release1),
# being the main output in monthly .txt.gz files in directories:
# - CHANGED_DATEPOS
# - CHANGED_IDS_UPDATE2
# - DUP_FILES
# - DUP_FILES_ID
#
# The reformat is towards having single files with:
# - report_id cdm_field_value changed/unchaged flag
# - grouped in subdirectories indicating the cdm field being modified
#
# as initially agreed and provided for...
#
# Reformatting of duplicate info needs script L1b_main_dup_merge.py as requires
# more than just separating columns
#
# Origin directories are hardcoded and assumed to be there, obviously,
# while output directories (../NOC_corrections/version/<correction>) are created if they don’t exist.
#
# DEV NOTES:
#
#
source r092019_setenv0.sh

datepos () {
  echo 'Processing DATEPOS files'
  origin_dir=$data_directory/$release/NOC_corrections/$version/origin/CHANGED_DATEPOS
  date_dir=$data_directory/$release/NOC_corrections/$version/timestamp
  latitude_dir=$data_directory/$release/NOC_corrections/$version/latitude
  longitude_dir=$data_directory/$release/NOC_corrections/$version/longitude

  if [ ! -d $date_dir ];then mkdir $date_dir;fi
  if [ ! -d $latitude_dir ];then mkdir $latitude_dir;fi
  if [ ! -d $longitude_dir ];then mkdir $longitude_dir;fi

  for filename in $(ls $origin_dir/????-??.txt.gz)
  do
      echo $filename
      out_name=$(basename $filename '.gz')
      zip_name=$(basename $filename)

      cat $filename | gunzip | awk 'BEGIN { FS = "|"; OFS = "|" } ;{print $1,$2,$3}' > $date_dir/$out_name
      gzip -f $date_dir/$out_name
      cat $filename | gunzip | awk 'BEGIN { FS = "|"; OFS = "|" } ;{print $1,$4,$5}' > $latitude_dir/$out_name
      gzip -f $latitude_dir/$out_name
      cat $filename | gunzip | awk 'BEGIN { FS = "|"; OFS = "|" } ;{print $1,$6,$7}' > $longitude_dir/$out_name
      gzip -f $longitude_dir/$out_name

  done
}

id () {
  echo "Processing ID files"
  origin_dir=$data_directory/$release/NOC_corrections/$version/origin/CHANGED_IDS_UPDATE2
  id_dir=$data_directory/$release/NOC_corrections/$version/id

  if [ ! -d $id_dir ];then mkdir $id_dir;fi

  for filename in $(ls $origin_dir/????-??.txt.gz)
  do
      echo $filename
      base_name=$(basename $filename)
      cp $filename $id_dir
  done
}

duplicates () {
  echo "Processing DUPLICATES files"
  origin_dir=$data_directory/$release/NOC_corrections/$version/origin/DUP_FILES
  origin_dir2=$data_directory/$release/NOC_corrections/$version/origin/DUP_FILES_ID
  dup_dir=$data_directory/$release/NOC_corrections/$version/duplicates
  flags_dir=$data_directory/$release/NOC_corrections/$version/duplicate_flags

  if [ ! -d $dup_dir ];then mkdir $dup_dir;fi
  if [ ! -d $flags_dir ];then mkdir $flags_dir;fi

  for filename1 in $(ls $origin_dir/????-??.txt.gz)
  do
      echo $filename
      base_name=$(basename $filename1)
      filename2=$origin_dir2/$base_name
      python $scripts_directory/L1b_main_dup_merge.py $filename1 $filename2 $flags_dir $dup_dir
  done
}

release=$1
version=$2

what=$3
case $what
in
    datepos) datepos ;;
    id) id ;;
    duplicates) duplicates ;;
    *) echo "Options are datepos,id or duplicates"
    exit ;;
esac
