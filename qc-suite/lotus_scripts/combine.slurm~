#!/bin/bash 
#BSUB -J recombine_[1945-2014]
#BSUB -q short-serial 
#BSUB -o ./logs_recombine/%J_%I.out 
#BSUB -e ./logs_recombine/%J_%I.err 
#BSUB -W 24:00
#BSUB -R "rusage[mem=64000]"
#BSUB -M 64000 

source ./setenv0.sh
cwd=`pwd`
cd ${working_directory}/corrected_data/

for month in "01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12"
do
cat ${LSB_JOBINDEX}-${month}-*.csv | grep -v "^YR|" | sort -t "|" -g -k 1,1 -k 2,2 -k 3,3 -k 4,4 -k 9,9 > ${LSB_JOBINDEX}-${month}.psv
done

cd $cwd

