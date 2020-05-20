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

# GET INPUT ARGUMENTS
script_config_file = sys.argv[1]
data_periods_file = sys.argv[2]
process_list_file = sys.argv[3]
failed_only = sys.argv[4]

failed_only = True if failed_only == 'y' else False

with open(script_config_file,'r') as fO:
    script_config = json.load(fO)
    
with open(data_periods_file,'r') as fO:
    data_periods = json.load(fO)
    
with open(process_list_file,'r') as fO:
    process_list = fO.read().splitlines()
    
dir_data = script_config.get('dir_data')
table = script_config.get('table')
dir_out = script_config.get('dir_out')
dir_log = os.path.join(dir_out,'log')
run_id = os.path.basename(script_config_file).split('.')[0]


for sid_dck in process_list: 
    ai = 0
    sid_dck_data_dir = os.path.join(dir_data,sid_dck)
    sid_dck_log_dir = os.path.join(dir_log,sid_dck)
    i_files = glob.glob(os.path.join(sid_dck_log_dir,'*-' + run_id + '.input'))
    for i_file in i_files:
        os.remove(i_file)
    init = datetime(data_periods.get().get('year_init'),1,1)
    end = datetime(data_periods.get().get('year_end'),1,1)
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=init, until=end):
        yyyy = str(dt.year)
        mm = str(dt.month.zfill(2))
        if failed_only and os.path.isfile('-'.join([yyyy,mm,run_id]) + '.ok'):
            continue
        if os.path.isfile(os.path.join(sid_dck_data_dir),'-'.join([table,yyyy,mm,'*'.psv])):    
            script_config.update({'sid_dck':sid_dck})
            script_config.update({'yyyy':yyyy})
            script_config.update({'mm':mm})
            ai_config_file = os.path.join(sid_dck_log_dir,str(ai) + '-' + run_id + '.input')

            with open(ai_config_file,'w') as fO:
                json.dump(script_config,fO,indent = 4)
            ai +=1
            
sys.exit(0)

