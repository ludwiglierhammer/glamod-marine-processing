# -*- coding: utf-8 -*-
"""

"""
import os
import sys
import json

FFS='-'

# GET INPUT ARGUMENTS
input_file =  sys.argv[1]
exit_status = sys.argv[2]
rm_input = sys.argv[3]

array_idx = os.path.basename(input_file).split('.')[0]
output_path = os.path.dirname(input_file)
output_file = os.path.join(output_path,array_idx + '.out')

# GET INFO FROM CONFIG FILE
with open(input_file,'r') as fO:
    config = json.load(fO)

release = config.get('release')
update = config.get('update')
yyyy = config.get('yyyy')
mm = config.get('mm')

# RENAME AND MOVE LSF OUTFILE
ext='ok' if exit_status == '0' else 'failed'
job_log_file = FFS.join([str(yyyy),str(mm),release,update]) + '.' + ext
job_log =  os.path.join(output_path,job_log_file)
os.rename(output_file,job_log)

# REMOVE *.input FILE
if rm_input == '0':
    os.remove(input_file)
