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
# while output directories (<release>/NOC_corrections/version/<correction>) are created if they don’t exist.
#
# DEV NOTES:
#
#
source ../setpaths.sh
source ../setenv0.sh

# FUNCTIONS -------------------------------------------------------------------
datepos () {
  echo 'Processing DATEPOS files'
  origin_dir=$origin_parent/CHANGED_DATEPOS
  date_dir=$destination_parent/timestamp
  latitude_dir=$destination_parent/latitude
  longitude_dir=$destination_parent/longitude

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
  origin_dir=$origin_parent/CHANGED_IDS_UPDATE2
  id_dir=$destination_parent/id

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
  origin_dir=$origin_parent/DUP_FILES
  origin_dir2=$origin_parent/DUP_FILES_ID
  dup_dir=$destination_parent/duplicates
  flags_dir=$destination_parent/duplicate_flags

  if [ ! -d $dup_dir ];then mkdir $dup_dir;fi
  if [ ! -d $flags_dir ];then mkdir $flags_dir;fi

  for filename1 in $(ls $origin_dir/????-??.txt.gz)
  do
      echo $filename
      base_name=$(basename $filename1)
      filename2=$origin_dir2/$base_name
      python $scripts_directory/noc_duplicates_merge.py $filename1 $filename2 $flags_dir $dup_dir
  done
}

# MAIN -------------------------------------------------------------------
release=$1
version=$2

origin_parent=$data_directory/datasets/NOC_corrections/$version
destination_parent=$data_directory/$release/NOC_corrections/$version

if [ ! -d $destination_parent ]
then
        echo 'Creating corrections destination directory '$destination_parent
	mkdir -p $destination_parent
fi

what=$3
case $what
in
    datepos) datepos ;;
    id) id ;;
    duplicates) duplicates ;;
    *) echo "Options are datepos,id or duplicates"
    exit ;;
esac
