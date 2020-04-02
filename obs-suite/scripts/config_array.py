# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import sys
import json

# GET INPUT ARGUMENTS
config_file = sys.argv[1]
data_path = sys.argv[2] 
sid_dck = sys.argv[3]
yyyy = sys.argv[4]
mm = sys.argv[5]

with open(config_file,'r') as fO:
    config = json.load(fO)
    
config.update({'data_directory':data_path})
config.update({'sid_dck':sid_dck})
config.update({'yyyy':yyyy})
config.update({'mm':mm})

with open(config_file,'w') as fO:
    json.dump(config,fO,indent = 4)

