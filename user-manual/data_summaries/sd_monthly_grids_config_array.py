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
    script_config.update({'year':dt.year})
    script_config.update({'month':dt.month})
    ai_config_file = os.path.join(sid_dck_log_dir,str(ai) + '-' + run_id + '.input')
    with open(ai_config_file,'w') as fO:
        json.dump(script_config,fO,indent = 4)
    return
# -----------------------------------------------------------------------------
    
# GET INPUT ARGUMENTS
data_path = sys.argv[1]
release = sys.argv[2]
dataset = sys.argv[3]
level = sys.argv[4]
table = sys.argv[5]
script_config_file = sys.argv[6]
data_periods_file = sys.argv[7]
process_list_file = sys.argv[8]
failed_only = sys.argv[9]

failed_only = True if failed_only == 'y' else False

if failed_only:
    print('Configuration using failed only mode')

with open(script_config_file,'r') as fO:
    main_config = json.load(fO)

script_config = main_config.get(table)
if not script_config:
   print('Table {0} not found in configuration file {1}'.format(table,script_config_file)) 
    
with open(data_periods_file,'r') as fO:
    data_periods = json.load(fO)
    
with open(process_list_file,'r') as fO:
    process_list = fO.read().splitlines()
    
level_dir = os.path.join(data_path,release,dataset,level)
#table = script_config.get('table')
dir_out = os.path.join(data_path,'user_manual','release_summaries',release,dataset)
dir_log = os.path.join(dir_out,'log')
run_id = os.path.basename(script_config_file).split('.')[0] + '-' + table

script_config.update({'dir_data':level_dir})
script_config.update({'dir_out':dir_out})

for sid_dck in process_list: 
    print(sid_dck)
    ai = 1
    sid_dck_data_dir = os.path.join(level_dir,sid_dck)
    sid_dck_log_dir = os.path.join(dir_log,sid_dck)
    i_files = glob.glob(os.path.join(sid_dck_log_dir,'*-' + run_id + '.input'))
    for i_file in i_files:
        os.remove(i_file)
    init = datetime(int(data_periods.get(sid_dck).get('year_init')),1,1)
    end = datetime(int(data_periods.get(sid_dck).get('year_end')),12,1)
    failed_files = glob.glob(os.path.join(sid_dck_log_dir,'*-' + run_id + '.failed'))
    if failed_only:
        if len(failed_files) > 0:
            print('{0}: found {1} failed jobs'.format(sid_dck,str(len(failed_files))))
            for failed_file in failed_files:
                os.remove(failed_file)
                yyyy,mm = os.path.basename(failed_file).split('-')[0:2]
                dt = datetime(int(yyyy),int(mm),1)
                if dt >= init and dt <= end:
                    config_element()
                    ai += 1
        else:
            print(sid_dck,': no failed files')
    else:
        print(sid_dck)            
        for dt in rrule.rrule(rrule.MONTHLY, dtstart=init, until=end):
            yyyy = str(dt.year)
            mm = str(dt.month).zfill(2)
            if len(glob.glob(os.path.join(sid_dck_data_dir,'-'.join([table,yyyy,mm,'*']) + '.psv'))) > 0:    
                config_element()
                ai +=1
    if len(failed_files) > 0:
        for x in failed_files:
            os.remove(x)       
sys.exit(0)

