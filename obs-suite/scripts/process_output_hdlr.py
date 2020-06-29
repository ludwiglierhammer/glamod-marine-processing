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
import shutil

FFS='-'

# GET INPUT ARGUMENTS
LSF_output_path = sys.argv[1] #/scratch-nompiio/<user_id>/  <release> <update> <dataset> <process> <data_level> <sid-dck> status
data_path = sys.argv[2] #/scratch-nompiio/<user_id>/  <release> <update> <dataset> <process> <data_level> <sid-dck> status
release = sys.argv[3]
update = sys.argv[4]
dataset = sys.argv[5]
process = sys.argv[6]
data_level = sys.argv[7]
sid_dck = sys.argv[8]
exit_status = sys.argv[9]

#GET LSF FILE
LSF_output_file = os.path.join(LSF_output_path,release,dataset,process,sid_dck,process + '.o')

job_log_dir = os.path.join(data_path,release,dataset,data_level,'log',sid_dck)

ext='ok' if exit_status == '0' else 'failed'
job_log_file = FFS.join([release,update,process]) + '.' + ext

job_log =  os.path.join(job_log_dir,job_log_file)

shutil.copy(LSF_output_file,job_log)
os.remove(LSF_output_file)

