#!/bin/bash

level=$1
sd=$2
table=$3

rMigration=/gws/nopw/j04/c3s311a_lot2/data/marine/rMigration/ICOADS_R3.0.0T/$level/$sd
r092019=/gws/nopw/j04/c3s311a_lot2/data/marine/r092019/ICOADS_R3.0.0T/$level/$sd

for file in $(ls $rMigration/$table*)
do
	echo 'Comparing...'
	base1=$(basename $file)
        echo $rMigration/$base1
	base2=$(basename $base1 rMigration-000000.psv)'r092019-000000.psv'
	echo $r092019/$base2
	diff <(cut -d \| -f 1-37 $rMigration/$base1) <(cut -d \| -f 1-37 $r092019/$base2)
done

