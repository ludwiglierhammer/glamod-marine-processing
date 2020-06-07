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
    dataset_name_dict = {}
    release_level2_dict = {}
    while True:
        release_name = input('Input name for release: ')
        if release_name == '':
            break
        release_name_list.append(release_name)
        dataset_name  = input('Input dataset name: ')
        dataset_name_dict[release_name] = dataset_name
        release_level2  = input('Input path to level2 configuration file: ')
        release_level2_dict[release_name] = release_level2

    print('Release and dataset names and level2 configuration paths are:')
    print(release_name_list)
    print(dataset_name_dict)
    print(release_level2_dict)
    i = input('Is this correct? Continue? (y/n)')
    if i == 'y':
        return release_name_list, dataset_name_dict, release_level2_dict
    else:
        return sys.exit(1)

  
# GET INPUT ARGUMENTS
release_names,dataset_names_dict,release_level2_dict = get_releases()

# GET OUTPUT PATH
out_path = input('Input filename and path for output: ')

merge_dicts = {}
for release_name in release_names:
    level2_path = release_level2_dict[release_name]
    with open(level2_path,'r') as f0:
        merge_dicts[release_name] = json.load(f0)

merged_dict = {"release_names" : release_names,"dataset_names" : dataset_names_dict}
global_init = min([ int(v.get('year_init')) for v in merge_dicts.values() ])
global_end = max([ int(v.get('year_end')) for v in merge_dicts.values() ])

merged_dict['year_init'] = global_init
merged_dict['year_end'] = global_end

params_exclude = []
for k,v in merge_dicts.items():
    params_exclude.extend(v.get('params_exclude',[]))
params_exclude = list(set(params_exclude))
merged_dict['params_exclude'] =  params_exclude

for k,v in merge_dicts.items():
    v.pop('year_init',None)
    v.pop('year_end',None)
    v.pop('params_exclude',None)

global_sd_list = []
for k,v in merge_dicts.items():
    global_sd_list.extend(v.keys())   
    
global_sd = list(set(global_sd_list))

for sd in global_sd:
    merged_dict[sd] = {}
    release_in = [ x for x in release_names if merge_dicts[x].get(sd) ]
    merged_dict[sd]['year_init'] = { release:int(merge_dicts[release][sd]['year_init']) for release in release_in }
    merged_dict[sd]['year_end'] = { release:int(merge_dicts[release][sd]['year_end']) for release in release_in }
    merged_dict[sd]['exclude'] = { release:merge_dicts[release][sd]['exclude'] for release in release_in }
    merged_dict[sd]['params_exclude'] = []
    for release in release_in:
        merged_dict[sd]['params_exclude'].extend(merge_dicts[release][sd].get('params_exclude',[]))    
    merged_dict[sd]['params_exclude'] = list(set(merged_dict[sd]['params_exclude']))
    if len(list(set(merged_dict[sd]['exclude'].values()))) > 1:
        print('WARNING, EXCLUDE OPTION DIFFERS BETWEEN DATA RELEASES SID-DCK {}'.format(sd))
    else:
        merged_dict[sd]['exclude'] = list(merged_dict[sd]['exclude'].values())[0]
  
with open(out_path,'w') as fO:
    json.dump(merged_dict,fO,indent=4)
       
sys.exit(0)

