# -*- coding: utf-8 -*-
"""
Spyder Editor

The following fails because the LSF_output_file and the job_log are in different mounts:
os.rename(LSF_output_file,job_log)
OSError: [Errno 18] Invalid cross-device link:

Have to cp and then remove!

This is a temporary script file.
"""
import os
import sys
import json
import shutil

FFS='-'

# GET INPUT ARGUMENTS
LSF_IDX = os.environ['LSB_JOBINDEX']
configfile =  sys.argv[1]
exit_status = sys.argv[2]
rm_input = sys.argv[3]

LSF_IDX = os.path.basename(configfile).split('.')[0]
LSF_output_path = os.path.dirname(configfile)
LSF_output_file = os.path.join(LSF_output_path,LSF_IDX + '.o')

# GET INFO FROM CONFIG FILE
with open(configfile,'r') as fO:
    config = json.load(fO) 

data_path = config.get('data_directory')
release = config.get('release')
update = config.get('update')
dataset = config.get('dataset')
data_level = config.get('job_config').get('data_level')
sid_dck = config.get('sid_dck')
yyyy = config.get('yyyy')
mm = config.get('mm')

# RENAME AND MOVE LSF OUTFILE
ext='ok' if exit_status == '0' else 'failed'
log_dir = os.path.join(data_path,release,dataset,data_level,'log',sid_dck)
job_log_file = FFS.join([str(yyyy),str(mm),release,update]) + '.' + ext
job_log =  os.path.join(log_dir,job_log_file)
shutil.copy(LSF_output_file,job_log)
os.remove(LSF_output_file)

# REMVE *.input FILE
#if rm_input == '0':
#    os.remove(configfile)
