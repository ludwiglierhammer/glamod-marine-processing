#!/bin/bash
release_migration=$1
release_ref=$2
level=$3
sd=$4
table=$5

ddata=/group_workspaces/jasmin2/glamod_marine/data
rM=$ddata/$release_migration/ICOADS_R3.0.0T/$level/$sd
rR=$ddata/$release_ref/ICOADS_R3.0.0T/$level/$sd

for file in $(ls $rM/$table*)
do
	base1=$(basename $file)
	base2=$(basename $base1 "$release_migration"-000000.psv)"$release_ref"'-000000.psv'
        if [ $table == 'header' ]
        then
                echo $base1 'VS'  $base2': comparing header table in 2 chunks'
		diff <(cut -d \| -f 1-37 $rM/$base1) <(cut -d \| -f 1-37 $rR/$base2)
        	diff <(cut -d"|" -f40- $rM/$base1) <(cut -d"|" -f40- $rR/$base2)
        else
		echo $base1 'VS'  $base2
		diff $rM/$base1 $rR/$base2
        fi
done

