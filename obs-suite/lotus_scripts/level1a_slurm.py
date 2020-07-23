#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 09:09:41 2020

@author: iregou
"""

import sys
import os
import json
import logging
import glob

import lotus_paths
import config_array


# Set process params-----------------------------------------------------------
LEVEL = 'level1a'
LEVEL_SOURCE = 'level0'
SOURCE_PATTERN = '????-??.imma'
PYSCRIPT = 'level1a.py'
CONFIG_FILE = 'level1a.json'
PERIODS_FILE = 'source_deck_periods.json'
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def check_file_exit(files):
    files = [files] if not isinstance(files,list) else files
    for filei in files:
        if not os.path.isfile(filei):
            logging.error('File {} does not exist. Exiting'.format(filei))
            sys.exit(1)
    return

def check_dir_exit(dirs):
    dirs = [dirs] if not isinstance(dirs,list) else dirs
    for diri in dirs:
        if not os.path.isdir(diri):
            logging.error('Directory {} does not exist. Exiting'.format(diri))
            sys.exit(1)
    return
#------------------------------------------------------------------------------


logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)

# Get process coordinates and build paths -------------------------------------
release = sys.argv[1]
update = sys.argv[2]
dataset = sys.argv[3]
config_path = sys.argv[4]
process_list_filename = sys.argv[5]

if len(sys.argv) > 6:
    failed_only = sys.argv[6]
    if failed_only == 'yes':
        failed_only = True
    elif failed_only == 'no':
        failed_only = False
    else:
        logging.error('Please input correct value for failed_only argument (yes/no). Exiting')
        sys.exit(1)
else:
    failed_only = False

# Get lotus paths
scripts_dir = lotus_paths.scripts_directory
data_dir = lotus_paths.data_directory
scratch_dir = lotus_paths.scratch_directory

# Build process specific paths
release_tag = '-'.join([release,update])
script_config_file = os.path.join(config_path,release_tag,dataset,CONFIG_FILE)
release_periods_file = os.path.join(config_path,release_tag,dataset,PERIODS_FILE)
process_list_file = os.path.join(config_path,release_tag,dataset,process_list_filename)
level_dir = os.path.join(data_dir,release,dataset,LEVEL)
level_source_dir = os.path.join(data_dir,'datasets',dataset,LEVEL_SOURCE)
log_dir = os.path.join(level_dir,'log')

# Check paths
check_file_exit([script_config_file,release_periods_file,process_list_file])
check_dir_exit([level_dir,level_source_dir,log_dir])

# Get configuration -----------------------------------------------------------
with open(script_config_file,'r') as fO:
    script_config = json.load(script_config_file)
    
with open(process_list_file,'r') as fO:
    process_list = fO.read().splitlines()

with open(release_periods_file,'r') as fO:
    release_periods = json.load(release_periods_file)
    
# Build array input files -----------------------------------------------------
status = config_array.main(level_source_dir,SOURCE_PATTERN,log_dir,
                           script_config,release_periods,process_list,
                           failed_only = failed_only) 
if status != 0:
    logging.error('Creating array inputs')
    sys.exit(1)
    
# Build jobs ------------------------------------------------------------------    
py_path = os.path.join(scripts_dir,PYSCRIPT)
pycommand='python {0} {1} {2} {3} {4}'.format(py_path,data_dir,release,update,
                  dataset)

for sid_dck in process_list:
    log_diri = os.path.join(log_dir,sid_dck)
    array_size = len(glob.glob(os.path.join(log_diri,'*.input')))
    if array_size == 0:
        logging.warning('No jobs for partition {}'.format(sid_dck))
        continue
    
    job_file = os.path.join(log_diri,sid_dck + '.slurm')
    t = '02:00:00'
    mem = '16000'
    
    with open(job_file) as fh:
        fh.writelines('#!/bin/bash\n')
        fh.writelines('#SBATCH --job-name={}.job\n'.format(sid_dck))
        fh.writelines('#SBATCH --array=1-{}\n'.format(str(array_size))  )            
        fh.writelines('#SBATCH --output={}/%a.out\n'.format(log_diri))
        fh.writelines('#SBATCH --error={}/%a.out\n'.format(log_diri))
        fh.writelines('#SBATCH --time={}\n'.format(t))
        fh.writelines('#SBATCH --mem={}\n'.format(mem))
        fh.writelines('#SBATCH --open-mode=truncate\n')
        fh.writelines('{0} {1}/%a.input\n'.format(pycommand,log_diri))
#
#    os.system("sbatch %s" %job_file)

        