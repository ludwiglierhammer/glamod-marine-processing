#!/bin/bash
for year in $(seq 1945 1 2014)
do
for month in "01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12"
do
cat ${year}-${month}-*.csv | grep -v "^YR|" | sort -t "|" -g -k 1,1 -k 2,2 -k 3,3 -k 4,4 -k 9,9 > ${year}-${month}.psv
done
done
