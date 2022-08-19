#!/bin/bash
#SBATCH --job-name=recombine
#SBATCH --array=2015-2021
#SBATCH --partition=short-serial
#SBATCH -o ./logs_recombine/%A_%a.out 
#SBATCH -e ./logs_recombine/%A_%a.err 
#SBATCH --time=24:00:00
#SBATCH --mem=64000

source ./setenv0.sh
cwd=`pwd`
cd ${working_directory}/corrected_data/

for month in "01" "02" "03" "04" "05" "06" "07" "08" "09" "10" "11" "12"
do
cat ${SLURM_ARRAY_TASK_ID}-${month}-*.csv | grep -v "^YR|" | sort -t "|" -g -k 1,1 -k 2,2 -k 3,3 -k 4,4 -k 9,9 > ${SLURM_ARRAY_TASK_ID}-${month}.psv
done

cd $cwd
