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

FFS='-'

# GET INPUT ARGUMENTS
LSF_input_file =  sys.argv[1]
exit_status = sys.argv[2]
rm_input = sys.argv[3]

LSF_IDX = os.path.basename(LSF_input_file).split('.')[0]
LSF_output_path = os.path.dirname(LSF_input_file)
LSF_output_file = os.path.join(LSF_output_path,LSF_IDX + '.o')

# GET INFO FROM CONFIG FILE
with open(LSF_input_file,'r') as fO:
    config = json.load(fO)

release = config.get('release')
update = config.get('update')
yyyy = config.get('yyyy')
mm = config.get('mm')

# RENAME AND MOVE LSF OUTFILE
ext='ok' if exit_status == '0' else 'failed'
job_log_file = FFS.join([str(yyyy),str(mm),release,update]) + '.' + ext
job_log =  os.path.join(LSF_output_path,job_log_file)
os.rename(LSF_output_file,job_log)

# REMOVE *.input FILE
if rm_input == '0':
    os.remove(LSF_input_file)
