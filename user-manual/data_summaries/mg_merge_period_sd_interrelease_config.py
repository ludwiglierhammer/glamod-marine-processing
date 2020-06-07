# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sys
import os
import glob
import json
from copy import deepcopy

# FUNCTIONS -------------------------------------------------------------------
def config_element():
    sd_config.update({'dir_data':sd_dir_data,'dir_out':sd_dir_out,
                      'start':sd_start,'stop':sd_stop})
    
    config_file = os.path.join(sd_log_dir,run_id + '.input')
    with open(config_file,'w') as fO:
        json.dump(sd_config,fO,indent = 4)
    return
# -----------------------------------------------------------------------------
    
# GET INPUT ARGUMENTS
log_path = sys.argv[1]
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

with open(script_config['level2_config'],'r') as fO:
    level2_config = json.load(fO)

run_id = os.path.basename(script_config_file).split('.')[0]

params_exclude_global = level2_config.get('params_exclude',[])

for sid_dck in process_list: 
    print(sid_dck)
    if level2_config.get(sid_dck).get('exclude'):
        print('Excluded from release')
        continue
    
    sd_log_dir = os.path.join(log_path,sid_dck)
    
    sd_config = deepcopy(script_config)
    sd_release = list(level2_config.get(sid_dck)['year_init'].keys())
    
    sd_params_exclude = deepcopy(params_exclude_global)
    sd_params_exclude.extend(level2_config.get(sid_dck).get('params_exclude',[]))
    sd_params_exclude = list(set(sd_params_exclude))
    for param in sd_params_exclude:
        sd_config['tables'].remove(param)
        
    sd_dir_out = os.path.join(sd_config.get('dir_out'),sid_dck)
    
    sd_dir_data = []
    sd_start = []
    sd_stop = []
    for release in sd_release:
        dir_data = sd_config.get('dir_data').get(release)
        start = level2_config.get(sid_dck).get('year_init').get(release)
        stop = level2_config.get(sid_dck).get('year_end').get(release)
        sd_dir_data.append(os.path.join(dir_data,sid_dck))
        sd_start.append(start)
        sd_stop.append(stop)
    
    i_files = glob.glob(os.path.join(sd_log_dir, run_id + '.input'))
    for i_file in i_files:
        os.remove(i_file)
    
    ok_files = glob.glob(os.path.join(sd_log_dir,run_id + '.ok'))    
    failed_files = glob.glob(os.path.join(sd_log_dir,run_id + '.failed'))
    if failed_only:
        if len(failed_files) > 0:
            print('{0}: found failed job'.format(sid_dck))
            config_element()
        else:
            print(sid_dck,': not failed job')
    else:
        if len(ok_files) > 0:
            for x in ok_files:
                os.remove(x)
        print(sid_dck)               
        config_element()
        
    if len(failed_files) > 0:
            for x in failed_files:
                os.remove(x)
    
            
sys.exit(0)

