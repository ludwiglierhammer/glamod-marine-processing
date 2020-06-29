#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Creates the directory tree for a new C3S user manual version 
in the user manual subspace

    
    Arguments
    ---------
    user_manual_path : str
        Path to the user manual space
    um_version : string
        Name for user manual version directory
    sd_file : string
        Path to file with sd list
          
    sd_file format:
    -------------------
    json with sid-dck as primary keys
    
        
"""

import os
import sys
import json


# Find command line arguments -------------------------------------------------
if len(sys.argv)>1:
     data_path = sys.argv[1]
     um_version = sys.argv[2]
     um_file = sys.argv[3]

# Functions -------------------------------------------------------------------
def create_subdir(lpath,subdir_list):
    subdir_list = [subdir_list] if isinstance(subdir_list,str) else subdir_list
    for subdir in subdir_list:
        subdir_dir = os.path.join(lpath,subdir)
        if not os.path.isdir(subdir_dir):
            os.mkdir(subdir_dir,0o774)

# Go --------------------------------------------------------------------------
subdirs = ['log']
deep_sublevels = ['log']
os.umask(0)
# READ LIST OF SID-DCKS FOR RELEASE
with open(um_file,'r') as fileO:
    sid_dck_dict = json.load(fileO)
    
sid_dck_dict.pop('release_names',None)
sid_dck_dict.pop('dataset_names',None)
sid_dck_dict.pop('year_init',None)
sid_dck_dict.pop('year_end',None)
sid_dck_dict.pop('params_exclude',None)

subdirs.extend(sid_dck_dict.keys())

um_path = os.path.join(data_path,um_version)
# CREATE DIR FOR UM VERSION
create_subdir(data_path,um_version)

# CREATE DIR FOR SOURCE
um_path = os.path.join(data_path,um_version)

# POPULATE LEVELS WITH SID-DCK AND LOG SUBDIRECTORIES
create_subdir(um_path,subdirs)

for sublevel in deep_sublevels:
    create_subdir(os.path.join(um_path,sublevel),sid_dck_dict.keys())
