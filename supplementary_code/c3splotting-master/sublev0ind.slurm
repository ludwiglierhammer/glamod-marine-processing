#!/bin/bash

#SBATCH --job-name=lev0ind
#SBATCH --output=lev0ind-%A_%a.o
#SBATCH --error=lev0ind-%A_%a.e

### tiny files

###SBATCH -p short-serial
###SBATCH --array=[110,119,143,145,150-152,155,184-189,194-197,201-216,218,221-227,229,230,233-235,239,241,242,245-249,255,281,500,666,667,701,702,708-711,715,720,721,730,731,734,736,740,750,761,781,782,796,849,850,874-882,889-891,893-902,928,996-997,999]
###SBATCH --time=00:15:00
###SBATCH --mem=1200

### small files

###SBATCH -p short-serial
###SBATCH --array=[117-118,144,255,555,704-707,735,762,888]
###SBATCH --time=01:00:00
###SBATCH --mem=3600

### medium files

###SBATCH -p short-serial
###SBATCH --array=[116,128,146,156,192,193,254,706,732,780,792-795,797,883,892,926,927,992,993]
###SBATCH --time=02:00:00
###SBATCH --mem=36000

### large files

###SBATCH -p high-mem
###SBATCH --array=[700,714,794,798,994,995]
###SBATCH --time=23:59:59
###SBATCH --mem=900000
#####SBATCH --mem=300000

module load jasr
Rscript do_level0.R $SLURM_ARRAY_TASK_ID $SLURM_ARRAY_TASK_ID
