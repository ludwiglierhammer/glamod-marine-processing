# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sys
import os
import glob
import json
from datetime import datetime

# FUNCTIONS -------------------------------------------------------------------
def config_element():
    script_config.update({'sid_dck':sid_dck})
    script_config.update({'year':int(yyyy)})
    script_config.update({'month':int(mm)})
    ai_config_file = os.path.join(sid_dck_log_dir,str(ai) + '-' + run_id + '.input')
    with open(ai_config_file,'w') as fO:
        json.dump(script_config,fO,indent = 4)
    return
# -----------------------------------------------------------------------------
    
# GET INPUT ARGUMENTS
dir_log = sys.argv[1]
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
    

run_id = os.path.basename(script_config_file).split('.')[0]

for sid_dck in process_list: 
    print(sid_dck)
    ai = 1
    sid_dck_log_dir = os.path.join(dir_log,sid_dck)
    if not os.path.isdir(sid_dck_log_dir):
        os.mkdir(sid_dck_log_dir)
    i_files = glob.glob(os.path.join(sid_dck_log_dir,'*-' + run_id + '.input'))
    for i_file in i_files:
        os.remove(i_file)

    ok_files = glob.glob(os.path.join(sid_dck_log_dir,'*-' + run_id + '.ok'))
    failed_files = glob.glob(os.path.join(sid_dck_log_dir,'*-' + run_id + '.failed'))
    header_files = glob.glob(os.path.join(script_config['dir_data'],sid_dck,'-'.join(['header','????','??','*']) + '.psv'))
    if failed_only:
        if len(failed_files) > 0:
            print('{0}: found {1} failed jobs'.format(sid_dck,str(len(failed_files))))
            for failed_file in failed_files:
                yyyy,mm = os.path.basename(failed_file).split('-')[0:2]
                config_element()
                ai += 1
        else:
            print(sid_dck,': no failed files')
    else:
        print(sid_dck) 
        if len(ok_files) > 0:
            for x in ok_files:
                os.remove(x)              
        for header_file in header_files:
            yyyy,mm = os.path.basename(header_file).split('-')[1:3]
            config_element()
            ai +=1
            
    if len(failed_files) > 0:
        for x in failed_files:
            os.remove(x)       
sys.exit(0)

