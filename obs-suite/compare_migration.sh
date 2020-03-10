#!/bin/bash

level=$1
sd=$2
table=$3

ddata=/group_workspaces/jasmin2/glamod_marine/data
rMigration=$ddata/Release2/ICOADS_R3.0.0T/$level/$sd
r092019=$ddata/r092019/ICOADS_R3.0.0T/$level/$sd

for file in $(ls $rMigration/$table*)
do
	base1=$(basename $file)
	base2=$(basename $base1 Release2-tests.psv)'r092019-000000.psv'
        if [ $table == 'header' ]
        then
                echo $base1 'VS'  $base2': comparing header table in 2 chunks'
		diff <(cut -d \| -f 1-37 $rMigration/$base1) <(cut -d \| -f 1-37 $r092019/$base2)
        	diff <(cut -d"|" -f40- $rMigration/$base1) <(cut -d"|" -f40- $r092019/$base2)
        else
		echo $base1 'VS'  $base2
		diff $rMigration/$base1 $r092019/$base2
        fi
done

