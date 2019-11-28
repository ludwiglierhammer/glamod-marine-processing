#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:24:10 2019

Script to aggregate equal monthly data derived from the level processing. 
    - looks for header-fileID-mmmm-yy.psv files
    - if any: 
        merges <table>-fileID*.psv
        recomputes corresponding fields in fileID.json and adds the leaking number to it
        recomputes the fileID.nc


The processing unit is the source-deck monthly file.

Input is in /data_path/<level>/dck_sid/table[i]-fileID*.psv
            /data_path/<level>/quicklooks/dck_sid/fileID.psv
            
Outputs data to  /data_path/release/<level>/dck_sid/table[i]-fileID.psv
Outputs quicklook info to /data_path/release/<level>/quicklooks/dck_sid/fileID.json/nc
where fileID is yyyy-mm-release-update
.....

@author: iregon
"""
import sys
import os
import json
import simplejson
import datetime
import glob
import logging
import subprocess
from imp import reload
reload(logging)  # This is to override potential previous config of logging

import cdm

# Functions--------------------------------------------------------------------
class script_setup:
    def __init__(self, inargs):
        self.data_path = inargs[1]
        self.sid_dck = inargs[2]
        self.year = inargs[3]
        self.month = inargs[4]
        self.release = inargs[5]
        self.update = inargs[6]
        self.source = inargs[7]
        self.level = inargs[8]

# This is for json to handle dates
date_handler = lambda obj: (
    obj.isoformat()
    if isinstance(obj, (datetime.datetime, datetime.date))
    else None
)

def build_io_dict():
    yyyy_mm = '-'.join([params.year,params.month])
    io_dict = {yyyy_mm:{}}
    for table in tables:
        io_dict[yyyy_mm][table] = {'total':0}
    return io_dict

def clean_level_leaks():
    level_from_baddate = glob.glob(os.path.join(level_path,'*' + filename_field_sep + level_id + filename_field_sep + '*.psv'))
    for filename in level_from_baddate:
        logging.info('Removing previous file: {}'.format(filename))
        os.remove(filename)

# MAIN ------------------------------------------------------------------------

# Process input and set up some things ----------------------------------------
logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)
if len(sys.argv)>1:
    logging.info('Reading command line arguments')
    args = sys.argv
else:
    logging.info('Using default arguments')

params = script_setup(args)
    
release_path = os.path.join(params.data_path,params.release,params.source)
   
level_path = os.path.join(release_path,params.level,params.sid_dck)
level_ql_path = os.path.join(release_path,params.level,'quicklooks',params.sid_dck)

data_paths = [level_path, level_ql_path]
if any([ not os.path.isdir(x) for x in data_paths ]):
    logging.error('Could not find data paths: '.format(','.join([ x for x in data_paths if not os.path.isdir(x)])))

filename_field_sep = '-'     
release_id = filename_field_sep.join([params.release,params.update ])    
level_id = filename_field_sep.join([str(params.year),str(params.month).zfill(2),release_id ])

tables = ['header','observations-at','observations-sst','observations-dpt',
                  'observations-wbt','observations-wd','observations-ws','observations-slp']
   
# Find if there's need to regroup ---------------------------------------------

main_file_name = os.path.join(level_path,filename_field_sep.join(['header',level_id]) + '.psv')
if len(glob.glob(main_file_name))==0:
    logging.warning('No main data stream for period {0}-{1}'.format(params.year,params.month))
    
io_file = os.path.join(level_ql_path,level_id + '.json')
if os.path.isfile(io_file):
    with open(io_file) as f:
        io_dict_mon = json.load(f)
else:
    io_dict_mon = build_io_dict() 

io_dict = io_dict_mon['-'.join([params.year,params.month])]

for table in tables:
    io_dict[table]['total'] = io_dict[table].get('total',0)
    io_dict[table]['date-misspositioned in'] = {} 
    io_dict[table]['date-misspositioned in']['total'] = 0 
    
leak_files = glob.glob(os.path.join(level_path,filename_field_sep.join(['header',level_id,'????' + filename_field_sep + '??.psv'])))
process = True

if len(leak_files)>0:
    logging.info('Files to regroup to {0}-{1} found: {2}'.format(params.year,params.month,str(len(leak_files))))    
else:
    logging.info('No files found to regroup to {0}-{1}'.format(params.year,params.month))
    process = False
    
if process:
    for table in tables:
        table_leaks = 0
        main_file_name = os.path.join(level_path,filename_field_sep.join([table,level_id]) + '.psv')
        main_file = glob.glob(main_file_name)
        leak_files = glob.glob(os.path.join(level_path,filename_field_sep.join([table,level_id,'????' + filename_field_sep + '??.psv'])))
        if len(leak_files) > 0:
            logging.info('Regrouping table {} files'.format(table))
            header_first = False
            if len(main_file) == 0:
                logging.warning('Main file {} not found'.format(main_file_name))
                logging.warning('Creating main file from first file to regroup {}'.format(leak_files[0]))
                header_first = True
            lfn = 0
            for lf in leak_files:
                yyyy_mm = os.path.basename(lf).split('.')[0][-7:]
                a = subprocess.run('awk \'END {print NR-1}\' ' + lf,shell=True,capture_output=True,encoding='utf-8')
                n_leaks = int(a.stdout)
                if lfn == 0 and header_first:
                    a = subprocess.run('awk \'NR==1 {print $0}\' ' + lf +' > ' + main_file_name ,shell=True,capture_output=True,encoding='utf-8')
                if n_leaks > 0:
                    a = subprocess.run('awk \'NR>1 {print $0}\' ' + lf +' >> ' + main_file_name ,shell=True,capture_output=True,encoding='utf-8')
                    io_dict[table]['date-misspositioned in'][yyyy_mm] = n_leaks
                    table_leaks += n_leaks
                lfn += 1
            io_dict[table]['date-misspositioned in']['total'] = table_leaks
            io_dict[table]['total'] = io_dict[table]['total'] + table_leaks
        else:
            logging.info('No files to regroup from table table {}'.format(table))
                
# Do the quick stats and save ql ----------------------------------------------
    logging.info('Computing gridded stats')
    cdm.gridded_stats.from_cdm_monthly(level_path, cdm_id = level_id, region = 'Global', 
                      resolution = 'lo_res', nc_dir = level_ql_path, qc=False)

#    And clean the leak files
    logging.info('Removing regrouped files')
    clean_level_leaks()

io_dict['date regrouped'] = datetime.datetime.now()
logging.info('Saving json quicklook')
level_io_filename = os.path.join(level_ql_path,level_id + '.json')
with open(level_io_filename,'w') as fileObj:
    simplejson.dump({'-'.join([params.year,params.month]):io_dict},fileObj,
                     default = date_handler,indent=4,ignore_nan=True)

# Now change permissions to output -------------------------------------------
# Quick thing. We remove this and set umask 002 in .bashrc file.
# Seems that changing permissions might not be possible if the user running is
# not the owner, even if write permissions....
#out_paths = [level_path,level_ql_path]
#logging.info('Changing output file permissions')
#for out_path in out_paths:
#    outfiles = glob.glob(os.path.join(out_path,'*' + level_id + '*'))
#    for outfile in outfiles:
#        os.chmod(outfile,0o664)
