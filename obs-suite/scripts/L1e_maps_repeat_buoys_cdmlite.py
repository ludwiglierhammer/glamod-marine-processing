#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:24:10 2019

Script to run the generation of individual monthly maps for level1e products

Script input:
------------

Configuration file:
------------------

.....

@author: iregon
"""

import sys
import os
import datetime
import cdm
import glob
import logging
import pandas as pd
from imp import reload
reload(logging)  # This is to override potential previous config of logging

# Functions--------------------------------------------------------------------
class script_setup:
    def __init__(self, inargs):
        self.data_path = inargs[1]
        self.sid_dck = inargs[2]
        self.dck = self.sid_dck.split("-")[1]
        self.year = inargs[3]
        self.month = inargs[4]
        self.release = inargs[5]
        self.update = inargs[6]
        self.source = inargs[7]


#------------------------------------------------------------------------------
           
# Some parameters
filename_field_sep = '-'
level = 'level1f'

# MAIN ------------------------------------------------------------------------
# Process input and set up some things and make sure we can do something-------
logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)
if len(sys.argv)>1:
    logging.info('Reading command line arguments')
    args = sys.argv
else:
    logging.error('Need arguments to run!')
    sys.exit(1)

params = script_setup(args)

release_path = os.path.join(params.data_path,params.release,params.source)
release_id = filename_field_sep.join([params.release,params.update ])
fileID = filename_field_sep.join([str(params.year),str(params.month).zfill(2),release_id ])
fileID_date = filename_field_sep.join([str(params.year),str(params.month)])

level_path = os.path.join(release_path,level,params.sid_dck)
level_ql_path = os.path.join(release_path,'level1e','quicklooks',params.sid_dck)

data_paths = [level_path, level_ql_path ]
if any([ not os.path.isdir(x) for x in data_paths ]):
    logging.error('Could not find data paths: {}'.format(','.join([ x for x in data_paths if not os.path.isdir(x)])))
    sys.exit(1)



header_filename = os.path.join(level_path,filename_field_sep.join(['header',fileID]) + '.psv')
if not os.path.isfile(header_filename):
    logging.error('Header table file not found: {}'.format(header_filename))
    sys.exit(1)

# Do some additional checks before clicking go
table = 'header'
header_df = pd.DataFrame()
header_df = cdm.read_tables(level_path,fileID,cdm_subset=[table],na_values='null')
if len(header_df) == 0:
    logging.error('Empty or non-existing header table')
    sys.exit(1)
    

# 3. NOW DO THE GRIDDED STATS -------------------------------------------------
#logging.info('Computing gridded stats: all reports')
#cdm.gridded_stats.from_cdm_monthly(level_path, cdm_id = fileID, region = 'Global', 
#                      resolution = 'lo_res', nc_dir = level_ql_path, qc=False)
#
#logging.info('Computing gridded stats: qced reports')
#cdm.gridded_stats.from_cdm_monthly(level_path, cdm_id = fileID, region = 'Global', 
#                      resolution = 'lo_res', nc_dir = level_ql_path, qc=[0,1])
#
#logging.info('Computing gridded stats: valid reports')
#cdm.gridded_stats.from_cdm_monthly(level_path, cdm_id = fileID, region = 'Global', 
#                      resolution = 'lo_res', nc_dir = level_ql_path, qc=[0])
 
logging.info('Computing gridded stats: all reports, all qc_reports')
cdm.gridded_stats.from_cdm_monthly(level_path, cdm_id = fileID, region = 'Global', 
                      resolution = 'lo_res', nc_dir = level_ql_path, qc=False,qc_report = False)

logging.info('Computing gridded stats: qced reports, qced qc_reports')
cdm.gridded_stats.from_cdm_monthly(level_path, cdm_id = fileID, region = 'Global', 
                      resolution = 'lo_res', nc_dir = level_ql_path, qc=[0,1],qc_report = [0,1])

logging.info('Computing gridded stats: valid reports, valid qc_reports')
cdm.gridded_stats.from_cdm_monthly(level_path, cdm_id = fileID, region = 'Global', 
                      resolution = 'lo_res', nc_dir = level_ql_path, qc=[0],qc_report = [0])
# Now change permissions to output -------------------------------------------
# Quick thing. We remove this and set umask 002 in .bashrc file.
# Seems that changing permissions might not be possible if the user running is
# not the owner, even if write permissions....
#out_paths = [level_ql_path]
#logging.info('Changing output file permissions')
#for out_path in out_paths:
#    outfiles = glob.glob(os.path.join(out_path,'*' + fileID + '*.nc'))
#    for outfile in outfiles:
#        os.chmod(outfile,0o664)
    
    
    
