#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:24:10 2019

Script to generate the C3S CDM Marine level1b data:
    
    - read linkage and duplicate identification output (previously pre-processed)
    - merge with CDM tables via record_id
    - re-assign dates
    - save tables to ascii

Uses modules cdm and pandas_operations to read CDM tables and handle corrections

The processing unit is the source-deck monthly set of CDM observation tables (header + observations-*).

Outputs data to /<data_path>/<release>/<dataset>/level1b/<sid-dck>/table[i]-fileID.psv
Outputs quicklook info to:  /<data_path>/<release>/<dataset>/level1b/quicklooks/<sid-dck>/fileID.json
where fileID is yyyy-mm-release_tag-update_tag

If any data in dataset yyyy-mm is identified to be in a different yyyy-mm (mainly after datetime corrections):
Outputs data to /<data_path>/<release>/<dataset>/level1b/<sid-dck>/table[i]-fileLeakID.psv        
where fileLeakID is yyyy-mm(real)-release_tag-update_tag-yyyy-mm(dataset)

Before processing starts:
    - checks the existence of all io subdirectories in level1a|b -> exits if fails
    - checks the existence of the dataset table to be converted (header only) -> exits if fails
    - removes all level1b products on input file resulting from previous runs

Inargs:
------
data_path: data release parent path (i.e./gws/nopw/c3s311_lot2/data/marine)
sid_dck: source-deck partition (sss-ddd)
year: data file year (yyyy)
month: data file month (mm)
release: release identifier
update: release update identifier
dataset: dataset identifier
configfile: path to configuration file with processing options


configfile:
-----------
json file with the following mappings:
- NOC_corrections version
- CDM tables elements with subdirectory prefix where corrections are in release/NOC_corrections/version
- subdirectory prefix with history event to append to history field


dev notes:
---------

1) Initially, file permission where changed to rwxrwxr-- to all output at
the end of the script with the lines below, however, it seemed that a user not
being the user that initially created the file could not do this...?? so in
the end it was decided to set umask 002 to the ./bashrc file

    out_paths = [L1b_path,L1b_ql_path]
    logging.info('Changing output file permissions')
    for out_path in out_paths:
        outfiles = glob.glob(os.path.join(out_path,'*' + fileID + '*'))
        for outfile in outfiles:
            os.chmod(outfile,0o664)
.....

@author: iregon
"""
import sys
import os
import simplejson
import json
import datetime
import cdm
import re
import numpy as np
from pandas_operations import replace
import glob
import logging
import pandas as pd
from imp import reload
reload(logging)  # This is to override potential previous config of logging


# Functions--------------------------------------------------------------------
class script_setup:
    def __init__(self, inargs):
        self.data_path = inargs[1]
        self.release = inargs[2]
        self.update = inargs[3]
        self.dataset = inargs[4]
        self.sid_dck = inargs[5]
        self.dck = self.sid_dck.split("-")[1]
        self.year = inargs[6]
        self.month = inargs[7]
        self.configfile =  inargs[8]
        
# This is for json to handle dates
date_handler = lambda obj: (
    obj.isoformat()
    if isinstance(obj, (datetime.datetime, datetime.date))
    else None
)

def clean_L1b(L1b_id):
    L1b_prods = glob.glob(os.path.join(L1b_path,'*-' + L1b_id + '.psv'))
    L1b_prods_idate = glob.glob(os.path.join(L1b_path,'*' + '-'.join([str(params.year),str(params.month).zfill(2)]) + '.psv'))
    L1b_ql = glob.glob(os.path.join(L1b_ql_path, L1b_id + '.*'))
    for filename in L1b_prods + L1b_prods_idate + L1b_ql:
        try:
            logging.info('Removing previous file: {}'.format(filename))
            os.remove(filename)
        except:
            pass

# MAIN ------------------------------------------------------------------------



# Process input and set up some things ----------------------------------------
logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)
if len(sys.argv)>1:
    logging.info('Reading command line arguments')
    args = sys.argv
else:
    logging.error('Need arguments to run!')
    sys.exit(1)

params = script_setup(args)


if not os.path.isfile(params.configfile):
    logging.error('Configuration file {} not found'.format(params.configfile))
    sys.exit(1)  
else:
    with open(params.configfile) as fileO:
        corrections = json.load(fileO)
    version_corrections = corrections.get('version')
    L1b_corrections = corrections.get('corrections')
    correction_histories = corrections.get('history explain')
    
filename_field_sep = '-' 
delimiter = '|'
cor_ext = '.txt.gz'
    
release_path = os.path.join(params.data_path,params.release,params.dataset)
release_id = filename_field_sep.join([params.release,params.update ]) 
fileID = filename_field_sep.join([str(params.year),str(params.month).zfill(2),release_id ])
fileID_date = filename_field_sep.join([str(params.year),str(params.month)])

L1a_path = os.path.join(release_path,'level1a',params.sid_dck)  
L1b_path = os.path.join(release_path,'level1b',params.sid_dck)
L1b_ql_path = os.path.join(release_path,'level1b','quicklooks',params.sid_dck)

L1b_main_corrections = os.path.join(params.data_path,params.release,'NOC_corrections',version_corrections)

logging.info('Setting corrections path to {}'.format(L1b_main_corrections))

data_paths = [L1a_path, L1b_path, L1b_ql_path, L1b_main_corrections ]
if any([ not os.path.isdir(x) for x in data_paths ]):
    logging.error('Could not find data paths: {}'.format(','.join([ x for x in data_paths if not os.path.isdir(x)])))
    sys.exit(1)

L1a_filename = os.path.join(L1a_path, 'header-' + fileID + '.psv')
if not os.path.isfile(L1a_filename):
    logging.error('L1a header file not found: {}'.format(L1a_filename))
    sys.exit(1)
 
# Clean previous L1a products and side files ----------------------------------
clean_L1b(fileID)
correction_dict = { table:{} for table in cdm.properties.cdm_tables}

# Do the data processing ------------------------------------------------------
isChange = '1'
dupNotEval = '4'
cdm_tables = cdm.lib.tables.tables_hdlr.load_tables()
# 1. Do it a table at a time....
history_tstmp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
for table in cdm.properties.cdm_tables:
    
    datetime_col = 'report_timestamp' if table == 'header' else 'date_time' 
    logging.info('TABLE {}'.format(table))
    table_df = pd.DataFrame()
    table_df = cdm.read_tables(L1a_path,fileID,cdm_subset=[table])
    
    if len(table_df) == 0:
        logging.warning('Empty or non-existing table {}'.format(table))
        correction_dict[table]['read'] = 0
        continue 

    table_df.set_index('report_id', inplace = True, drop = False)
    correction_dict[table]['read'] = len(table_df)
    
    table_corrections = L1b_corrections.get(table)
    if len(table_corrections) == 0:
        logging.warning('No corrections defined for table {}'.format(table))
        continue
    
    correction_dict[table]['date-misspositioned out'] =  {}
    correction_dict[table]['date-misspositioned in'] =  {}
    correction_dict[table]['corrections'] =  {}
    
    for correction,element in table_corrections.items():
        correction_dict[table]['corrections'][element] = {'applied':1,'number':0}
        logging.info('Applying corrections for element {}'.format(element))
        cor_path = os.path.join(L1b_main_corrections,correction, fileID_date + cor_ext)
        if not os.path.isfile(cor_path):
            logging.warning('Correction file {} not found'.format(cor_path))
            continue
        
        columns = ['report_id',element,element + '.isChange']
        correction_df =  pd.read_csv(cor_path, delimiter = delimiter, dtype = 'object',
                           header = None, usecols=[0,1,2], names = columns,
                           quotechar=None,quoting=3)
        if len(correction_df)>0:
            correction_df.set_index('report_id', inplace = True, drop = False)
            try:
                correction_df = correction_df.loc[table_df.index]
            except:
                logging.warning(logging.warning('No {} corrections matching'.format(correction)))
                continue

        correction_dict[table]['corrections'][element]['applied'] = 0
        table_df[element + '.former'] = table_df[element]
        table_df[element + '.isChange'] = ''
        table_df = replace.replace_columns(table_df, correction_df, pivot_c = 'report_id',
                   rep_c = [element,element + '.isChange'])
        table_df.set_index('report_id', inplace = True, drop = False) # because it gets reindexed in every replacement....
        replaced = table_df[element + '.isChange'] == isChange
        
        not_replaced = table_df[element + '.isChange'] != isChange
        table_df[element].loc[not_replaced] = table_df[element + '.former'].loc[not_replaced]
        correction_dict[table]['corrections'][element]['number']  = len(np.where(replaced)[0])
        logging.info('No. of corrections applied {}'.format(correction_dict[table]['corrections'][element]['number']))
        # THIS IS A DIRTY THNIG TO DO, BUT WILL LEAVE IT AS IT IS FOR THIS RUN:
        # we only keep a lineage of the changes applied to the header
        # (some of these are shared with obs tables like position and datetime, although the name for the cdm element might not be the same....)
        if table == 'header':
            table_df['history'].loc[replaced] = table_df['history'].loc[replaced] + ';{0}. {1}'.format(history_tstmp,correction_histories.get(correction))
            
        table_df.drop(element + '.former',axis = 1)
        table_df.drop(element + '.isChange',axis = 1)

    # Track duplicate status
    if table == 'header':
        correction_dict['duplicates']= {}
        contains_info = table_df['duplicate_status'] != dupNotEval
        logging.info('Logging duplicate status info')
        if len(np.where(contains_info)[0])>0:
            counts = table_df['duplicate_status'].value_counts()
            for k in counts.index:
                correction_dict['duplicates'][k] = int(counts.loc[k]) # otherwise prints null to json!!!
        else:
            correction_dict['duplicates'][dupNotEval] =  correction_dict[table]['read'] 
        
    # Now get ready to write out, extracting eventual leaks of data to a different monthly table
    cdm_columns = cdm_tables.get(table).keys()
    header = True 
    wmode = 'w'
    # BECAUSE LIZ'S datetimes have UTC info:
    #ValueError: Tz-aware datetime.datetime cannot be converted to datetime64 unless utc=True
    table_df['monthly_period'] = pd.to_datetime(table_df[datetime_col],errors='coerce',utc=True).dt.to_period('M')
    monthly_periods = list(table_df['monthly_period'].dropna().unique())
    source_mon_period = pd.Series(data=[datetime.datetime(int(params.year),int(params.month),1)]).dt.to_period('M').iloc[0]
    table_df['monthly_period'].fillna(source_mon_period,inplace=True)
    table_df.set_index('monthly_period',inplace=True,drop=True)
    
    len_df = len(table_df)
    if source_mon_period in monthly_periods:
        logging.info('Writing {0} data to {1} table file'.format(source_mon_period.strftime('%Y-%m'),table))
        filename = os.path.join(L1b_path,filename_field_sep.join([table,fileID]) + '.psv')
        table_df.loc[[source_mon_period],:].to_csv(filename, index = False, sep = delimiter, columns = cdm_columns
                 ,header = header, mode = wmode)
        table_df.drop(source_mon_period,inplace=True)
        len_df_i = len_df
        len_df = len(table_df)
        correction_dict[table]['total'] = len_df_i - len_df
    else:
        correction_dict[table]['total'] = 0
        logging.warning('No original period ({0}) data found in table {1} after datetime reordering'.format(source_mon_period.strftime('%Y-%m'),table))
    
    datetime_leaks = [ m for m in monthly_periods if m != source_mon_period ]
    if len(datetime_leaks)>0:
        logging.info('Datetime leaks found:')
        for leak in datetime_leaks:
            logging.info('Writing {0} data to {1} table file'.format(leak.strftime('%Y-%m'),table))
            L1b_idl = filename_field_sep.join([table,leak.strftime('%Y-%m'),release_id,source_mon_period.strftime('%Y-%m')])
            filename = os.path.join(L1b_path,L1b_idl + '.psv')
            table_df.loc[[leak],:].to_csv(filename, index = False, sep = delimiter, columns = cdm_columns
                 ,header = header, mode = wmode)
            table_df.drop(leak,inplace=True)
            len_df_i = len_df
            len_df = len(table_df)
            correction_dict[table]['date-misspositioned out'][leak.strftime("%Y-%m")] = len_df_i - len_df  
        correction_dict[table]['date-misspositioned out']['total'] = sum([ v for k,v in correction_dict[table]['date-misspositioned out'].items()])
    else:
        correction_dict[table]['date-misspositioned out']['total'] = 0


correction_dict['date processed'] = datetime.datetime.now()

logging.info('Saving json quicklook')
L1b_io_filename = os.path.join(L1b_ql_path,fileID + '.json')
with open(L1b_io_filename,'w') as fileObj:
    simplejson.dump({'-'.join([params.year,params.month]):correction_dict},fileObj,
                     default = date_handler,indent=4,ignore_nan=True)

