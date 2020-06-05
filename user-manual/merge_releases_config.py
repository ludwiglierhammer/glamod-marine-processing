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

def get_releases():
    release_name_list = []
    dataset_name_list = []
    release_level2_list = []
    while True:
        release_name = input('Input name for release: ')
        if release_name == '':
            break
        release_name_list.append(release_name)
        dataset_name  = input('Input dataset name: ')
        dataset_name_list.append(dataset_name)
        release_level2  = input('Input path to level2 configuration file: ')
        release_level2_list.append(release_level2)
e
    print('Release and dataset names and level2 configuration paths are:')
    print(release_name_list)
    print(dataset_name_list)
    print(release_level2_list)
    i = input('Is this correct? Continue? (y/n)')
    if i == 'y':
        return release_name_list, dataset_name_list, release_level2_list
    else:
        return sys.exit(1)

  
# GET INPUT ARGUMENTS
release_names,dataset_names,release_level2_list = get_releases()

# GET OUTPUT PATH
out_path = input('Input filename and path for output: ')

merge_dicts = {}
for release_name,level2_path in zip(release_names,release_level2_list):
    merge_dicts[release_name] = json.load(level2_path)

merged_dict = {"release_names" : release_names,"dataset_names" : dataset_names}

global_init = min([ v.get('year_init') for v in merge_dicts.values() ])
global_end = max([ v.get('year_end') for v in merge_dicts.values() ])

merged_dict['year_init'] = global_init
merged_dict['year_end'] = global_end

params_exlude = { k:v.get('params_exclude') for k,v in merge_dicts }

for k,v in merge_dicts:
    k.pop('year_init')
    k.pop('year_end')
    k.pop('params_exclude')

global_sd_list = []
for k,v in merge_dicts.items():
    global_sd_list.extend(v.keys())   
    
global_sd = list(set(global_sd_list))

for sd in global_sd:
    merged_dict[sd] = {}
    release_in = [ x for x in release_names if merge_dicts[release_names].get(sd) ]
    merged_dict[sd]['year_init'] = { release:merge_dicts[release][sd]['year_init'] for release in release_in }
    merged_dict[sd]['year_end'] = { release:merge_dicts[release][sd]['year_end'] for release in release_in }
    merged_dict[sd]['exclude'] = { release:merge_dicts[release][sd]['exclude'] for release in release_in }
    merged_dict[sd]['params_exclude'] = { release:merge_dicts[release][sd]['params_exclude'] for release in release_in }
  
with open(out_path,'w') as fO:
    json.dump(merged_dict,fO,indent=4)
       
sys.exit(0)

