#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 16:18:36 2019

Create initial level2 product list from the initial source-data list

Outputs file to /<data_path>/<release>/<source>/level2/L2-config.json

Inargs:
------
data_path: data release parent path (i.e./gws/nopw/c3s311_lot2/data/marine)
release: release identifier
update: release update identifier
dataset:  dataset directory identifier (ie.e ICOADS_R3.0.0T)
config_file: path to release/update list

@author: iregon
"""

import os
import sys
import pandas as pd
import json

# Find command line arguments -------------------------------------------------
if len(sys.argv)>1:
     data_path = sys.argv[1]
     release = sys.argv[2]
     update = sys.argv[3]
     source = sys.argv[4]
     release_file = sys.argv[5]
# -----------------------------------------------------------------------------   
level = 'level2'
release_path = os.path.join(data_path,release,source)
filename_field_sep = '-'  
  
level_path = os.path.join(release_path,level)  
level_filename = os.path.join(level_path,'L2-config.json')


sid_dck_list = pd.read_csv(release_file,names= ['sid-dck','init','end'],header = None,delimiter='\t')

level2_dict = {}
level2_dict = {'params_exclude':[]}
for sid_dck in sid_dck_list['sid-dck']:
    level2_dict[sid_dck] = {'exclude':False,'params_exclude':[]}

with open(level_filename,'w') as fileObj:
    json.dump(level2_dict,fileObj,indent=4)    
