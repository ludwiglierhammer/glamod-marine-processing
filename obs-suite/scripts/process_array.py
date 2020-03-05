# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import os
import sys
import subprocess
import json


# GET LSF ARRAY INDEX
LSF_IDX = os.environ['LSB_JOBINDEX']

# GET INPUT ARGUMENTS
LSF_output_path = sys.argv[1] 
data_path = sys.argv[2]
release = sys.argv[3]
update = sys.argv[4]
dataset = sys.argv[5]
process = sys.argv[6]
data_level = sys.argv[7]
sid_dck = sys.argv[8]
process_config_file = sys.argv[9]

# GET ARRAY YYYY MM
LSF_input_file = os.path.join(LSF_output_path,release,dataset,process,sid_dck,str(LSF_IDX) + '.input')

with open(LSF_input_file,'r') as fO:
    job_config = json.load(fO)


yyyy = job_config.get('yyyy')
mm = job_config.get('mm')

with open(process_config_file,'r') as fO:
    config = json.load(fO)

script_path = os.path.dirname(os.path.abspath(__file__))
script_name = config.get('job').get('script_name')
script = os.path.join(script_path,script_name)

#print(' '.join(['python',script,data_path,release,update,dataset,sid_dck,yyyy,mm,process_config_file]))
returncode = subprocess.call(['python',script,data_path,release,update,dataset,sid_dck,yyyy,mm,process_config_file])
# Watch THIS!!!!
#returncode = 0
sys.exit(returncode)
