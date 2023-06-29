#!/bin/bash
#SBATCH -p high-mem
#SBATCH --array=[100,200,700,800,900]
#SBATCH --job-name=lev2h
#SBATCH --output=lev2h-%A_%a.o
#SBATCH --error=lev2h-%A_%a.e
#SBATCH --time=23:59:59
#SBATCH --mem=300000
module load jasr/4.0/r20211110
Rscript do_level2.R $SLURM_ARRAY_TASK_ID
