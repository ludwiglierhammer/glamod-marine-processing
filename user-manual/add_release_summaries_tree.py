#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 12:29:06 2019

Creates the directory tree for a new C3S data release and source or for a new
source in a pre-existing release

Inargs:
------

user_manual_path: directory where user_manual is
release_name: name for release directory
source_name: name for data source in directory tree
release_file: path to file with individual sid-dck

release_file format:
-------------------
json with sid-dck as primary keys

@author: iregon
"""

import os
import sys
import json


# Find command line arguments -------------------------------------------------
if len(sys.argv)>1:
     data_path = sys.argv[1]
     release_name = sys.argv[2]
     source_name = sys.argv[3]
     release_file = sys.argv[4]

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
with open(release_file,'r') as fileO:
    sid_dck_dict = json.load(fileO)

subdirs.extend(sid_dck_dict.keys())

# CREATE DIR FOR RELEASE
release_tag = release_name
create_subdir(data_path,release_tag)

# CREATE DIR FOR SOURCE
release_path = os.path.join(data_path,release_tag)
create_subdir(release_path, source_name)

# POPULATE LEVELS WITH SID-DCK AND LOG SUBDIRECTORIES
source_path = os.path.join(release_path, source_name)

create_subdir(source_path,subdirs)

for sublevel in deep_sublevels:
    create_subdir(os.path.join(source_path,sublevel),sid_dck_dict.keys())
