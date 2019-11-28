#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:24:10 2019

Script to generate the C3S level0 data.

    - Reads sid-dck and associated data periods from the release_file 
    - Copies corresponding data files from source directory to release directory
    - Data files are assumed to be already formatted and partitioned according
    to C3S level0 requirements in the source directory:
        /<source_directory>/<sid-dck>/monthly_files.ext
    - Release-source level0 directory tree is assumed to be already built:
        /<level0_path>/<sid-dck>/    
    - Cleans /<level0_path>/<sid-dck>/ before copying any data

Inargs:
------
source_path = sys.argv[1]
level0_path = sys.argv[2]
release_file = sys.argv[3]

release_file format:
-------------------
header: no   
delimiter: tab
columns: sid-dck, yr-mo (init), yr-mo (end)

dev notes:
---------
For this release, file format is only IMMA1 and therefore source
filename patterns are here hard-parameterized as 'yyyy-mm.imma'

This can be quite slow for a full release, maybe better to run at the sid-dck
level from a launcher script in a future version, somethin like:
    L0_main.py source_path level0_path sid-dck yr mo yr mo
       
This works at 'monthly' precission, do we want just to do the years?    

Mmm, do we better add datapath, release and source to inargs instead of level0_path and
build this from datapath,release and source like in the rest of levels?

.....

@author: iregon
"""
import sys
import os
import glob
import logging
import pandas as pd
import shutil
import datetime
from imp import reload
reload(logging)  # This is to override potential previous config of logging


# Functions--------------------------------------------------------------------
def clean_L10(L10_path):
    L10_prods = glob.glob(os.path.join(L10_path,'*.*'))
    for filename in L10_prods:
        try:
            logging.info('Removing previous file: {}'.format(filename))
            logging.warning('Removing previous file disabled: potentially dangerous....')
            #os.remove(filename)
        except:
            pass

def month_year_iter( start_month, start_year, end_month, end_year ):
    ym_start= 12*start_year + start_month - 1
    ym_end= 12*end_year + end_month 
    for ym in range( ym_start, ym_end ):
        y, m = divmod( ym, 12 )
        yield y, m+1 
# MAIN ------------------------------------------------------------------------

# Process input and set up some things ----------------------------------------
if len(sys.argv)>1:
    print('Reading command line arguments')
    source_path = sys.argv[1]
    level0_path = sys.argv[2]
    release_file = sys.argv[3]
else:
    print('ERROR: need command line arguments')
    sys.exit(1)
    
filename_field_sep = '-' 
file_id = '????-??.imma' 
list_file_base = os.path.basename(release_file).split('.')[0]        
logfile = os.path.join(level0_path,list_file_base + filename_field_sep + datetime.datetime.today().strftime('%Y%m%d') + '.log')        
logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=logfile)

       
if any([ not os.path.isdir(x) for x in [source_path,level0_path] ]):
    logging.error('Could not find data paths: '.format(','.join([ x for x in [source_path,level0_path] if not os.path.isdir(x)])))
    sys.exit(1)

if any([ not os.path.isfile(x) for x in [release_file] ]):
    logging.error('Could not find input files: '.format(','.join([ x for x in [release_file] if not os.path.file(x)])))
    sys.exit(1)

# Copy the data         -------------------------------------------------------
release_list = pd.read_csv(release_file,delimiter='\t',header = None,
                               names=['sid-dck','init','end'],dtype = 'object')

release_list[['init_yr','init_mo']] = pd.DataFrame(release_list['init'].str.split('-').to_list(),columns = ['init_yr','init_mo']).astype(int)
release_list[['end_yr','end_mo']] = pd.DataFrame(release_list['end'].str.split('-').to_list(),columns = ['end_yr','end_mo']).astype(int)

for row in release_list[['sid-dck','init_yr','init_mo','end_yr','end_mo']].values:
    sid_dck = row[0]
    source_path_sd = os.path.join(source_path,sid_dck)
    level0_path_sd = os.path.join(level0_path,sid_dck)
    source_ini = datetime.datetime(row[1],row[2],1)
    source_end = datetime.datetime(row[3],row[4],1)
    logging.info('init {}'.format(source_ini.strftime('%Y%m%d')))
    logging.info('end {}'.format(source_end.strftime('%Y%m%d')))
    if any([ not os.path.isdir(x) for x in [source_path_sd,level0_path_sd] ]):
        logging.error('Could not find data paths: '.format(','.join([ x for x in [source_path_sd,level0_path_sd] if not os.path.isdir(x)])))
        continue
    clean_L10(level0_path_sd)
    source_files = glob.glob(os.path.join(source_path_sd,file_id))
    source_files_process = source_files.copy()
    
    if len(source_files) > 0:
        for file in source_files:
            yr,mo = os.path.basename(file).split(".")[0].split("-")
            file_dt = datetime.datetime(int(yr),int(mo),1)
            if not source_ini <= file_dt <= source_end:
                source_files_process.remove(file)
                logging.info('Removing file {} from copy list'.format(file))
    else:
        logging.warning('No files found for {0}'.format(sid_dck))
        continue
            
    if len(source_files_process) > 0:
        for file in source_files_process:
            logging.info('Copying {0} to {1}'.format(file,level0_path_sd))
            shutil.copy(file,level0_path_sd)
    else:
        logging.warning('No files selected for {0} in period {1}-{2}'.format(sid_dck,source_ini.strftime('%Y%m%d'),source_end.strftime('%Y%m%d')))
        continue    
    

