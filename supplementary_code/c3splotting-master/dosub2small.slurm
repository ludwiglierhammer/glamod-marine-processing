#!/bin/bash
#SBATCH -p short-serial
#SBATCH --array=[500,600]
#SBATCH --job-name=lev2
#SBATCH --output=lev2-%A_%a.o
#SBATCH --error=lev2-%A_%a.e
#SBATCH --time=23:59:59
#SBATCH --mem=64000
module load jasr/4.0/r20211110
Rscript do_level2.R $SLURM_ARRAY_TASK_ID
