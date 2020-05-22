# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sys
import os
import glob
import json
from dateutil import rrule
from datetime import datetime

# FUNCTIONS -------------------------------------------------------------------
def config_element():
    script_config.update({'sid_dck':sid_dck})
    config_file = os.path.join(sid_dck_log_dir,run_id + '.input')
    with open(config_file,'w') as fO:
        json.dump(script_config,fO,indent = 4)
    return
# -----------------------------------------------------------------------------
    
# GET INPUT ARGUMENTS
data_path = sys.argv[1]
script_config_file = sys.argv[2]
process_list_file = sys.argv[3]
failed_only = sys.argv[4]

failed_only = True if failed_only == 'y' else False

if failed_only:
    print('Configuration using failed only mode')

with open(script_config_file,'r') as fO:
    script_config = json.load(fO)

    
with open(process_list_file,'r') as fO:
    process_list = fO.read().splitlines()
    
dir_log = os.path.join(data_path,'log')
run_id = os.path.basename(script_config_file).split('.')[0]

script_config.update({'dir_data':data_path})

for sid_dck in process_list: 
    print(sid_dck)
    sid_dck_data_dir = os.path.join(data_path,sid_dck)
    sid_dck_log_dir = os.path.join(dir_log,sid_dck)
    i_files = glob.glob(os.path.join(sid_dck_log_dir, run_id + '.input'))
    for i_file in i_files:
        os.remove(i_file)

    if failed_only:
        failed_files = glob.glob(os.path.join(sid_dck_log_dir,run_id + '.failed'))
        if len(failed_files) > 0:
            for x in failed_files:
                os.remove(x)
            print('{0}: found failed job'.format(sid_dck))
            config_element()

        else:
            print(sid_dck,': not failed job')
    else:
        print(sid_dck)               
        config_element()
            
sys.exit(0)

