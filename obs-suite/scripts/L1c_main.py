#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:24:10 2019

Script to generate the C3S CDM Marine level1c data: validate 
header.report_timestamp and header.primary_station_id and apply outcome to rest
of tables, rejecting reports not validating any of these two fields.
    
    - Read header data
    
    - Initialized mask for id and datetime to True
    
    - Validate header.report_timestamp (see Notes below)
    - Validate header.primary_station_id (see Notes below)
    This process will fail and exit if the corresponding id corrections file
    is not found in level1b
    
    - Output all reports not validating timestamp to:
        -> /level1c/invalid/sid-dck/header-fileID-report_timsetamp.psv
    - Output all reports not validating primary_station_id to:
        -> /level1c/invalid/sid-dck/header-fileID-primary_station_id.psv
    
    - Merge report_timestamp and primary_station_id in a single validation rule
    (fila if any fails)
    - Drop corresponding records from all tables
    
    - Log to json dropped per table per validated field and final numer of 
    records in the resulting tables
    - Log to json unique primary_station_id counts
    - Log to json primary_station_id validation rules numbers:
        1. callsings
        2. rest
        3. restored because output from Liz's process

The processing unit is the source-deck monthly set of CDM tables.

Outputs data to /<data_path>/<release>/<source>/level1c/<sid-dck>/table[i]-fileID.psv
Outputs invlid data to /<data_path>/<release>/<source>/level1c/invalid/<sid-dck>/table[i]-fileID-invalid_field.psv
Outputs quicklook info to:  /<data_path>/<release>/<source>/level1c/quicklooks/<sid-dck>/fileID.json

where fileID is yyyy-mm-release_tag-update_tag

Before processing starts:
    - checks the existence of all io subdirectories in level1b|c -> exits if fails
    - checks the existence of the source table to be converted (header only) -> exits if fails
    - removes all level1c products on input file resulting from previous runs

Inargs:
------
data_path: data release parent path (i.e./gws/nopw/c3s311_lot2/data/marine)
sid_dck: source-deck partition (sss-ddd)
year: data file year (yyyy)
month: data file month (mm)
release: release identifier
update: release update identifier
source: source dataset identifier

Notes on validations:
--------------------
** HEADER.REPORT_TIMESTAMP VALIDATION **
This validation is just trying to convert to a datetime object the content of
the field. Where empty, this conversion (and validation) will fail. 
And will be empty if during the mapping in level1a the report_timestamp could 
not be built from the source data, or if there was any kind of messing in level1b
datetime corrections......

** HEADER.PRIMARY_STATION_ID VALIDATION **
Due to various reasons, the validation is done in 3 stages and using different methods:
    1. Callsign IDs: use set of validation patterns harcoded here
    2. Rest of IDs: use set of per dck validation patterns in metmetpy module
    3. All: read Liz's ID replacement files (level1b) and make sure all the IDs
    that were modified in this process validate to True. This is this crappy because
    there is no clean way to find out if the id was modified from the CDM fields.

Dev notes:
----------
1) This script is fully tailored to the idea of how validation and cleaning should
be at the time of developing it. It is not parameterized and is hardly flexible.

2) Why don't we just pick the NaN dates as invalid, instead of looking where conversion
fails?

3) Initially, file permission where changed to rwxrwxr-- to all output at
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
import datetime
import cdm
import numpy as np
import glob
import logging
import pandas as pd
import re
from metmetpy.station_id import validate as validate_id
from imp import reload
reload(logging)  # This is to override potential previous config of logging

# FUNCTIONS -------------------------------------------------------------------
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

# This is for json to handle dates
date_handler = lambda obj: (
    obj.isoformat()
    if isinstance(obj, (datetime.datetime, datetime.date))
    else None
)

def process_table(table_df,table_name):
    if isinstance(table_df,str):
        # Open table and reindex
        table_df = pd.DataFrame()
        table_df = cdm.read_tables(prev_level_path,fileID,cdm_subset=[table_name])
        if table_df is None or len(table_df) == 0:
            logging.warning('Empty or non existing table {}'.format(table_name))
            return
        table_df.set_index('report_id', inplace = True, drop = False)
     
    odata_filename = os.path.join(level_path,filename_field_sep.join([table_name,fileID]) + '.psv')
    cdm_columns = cdm_tables.get(table_name).keys()
    table_mask = mask_df.loc[table_df.index]
    if table_name == 'header':
            table_df['history'] = table_df['history'] + ';{0}. {1}'.format(history_tstmp,history_explain)
            validation_dict['unique_ids'] = table_df.loc[table_mask['all'],'primary_station_id'].value_counts(dropna=False).to_dict()
    
    if len(table_df[table_mask['all']]) > 0:
        table_df[table_mask['all']].to_csv(odata_filename, index = False, sep = delimiter, columns = cdm_columns
                     ,header = header, mode = wmode, na_rep = 'null')
    else:
        logging.warning('Table {} is empty. No file will be produced'.format(table_name))
     
    validation_dict[table_name] = {}
    validation_dict[table_name]['total'] = len(table_df[table_mask['all']])
    return

def clean_level(file_id):
    level_prods = glob.glob(os.path.join(level_path,'*-' + file_id + '.psv'))
    level_logs = glob.glob(os.path.join(level_log_path, file_id + '.*'))
    level_ql = glob.glob(os.path.join(level_ql_path, file_id + '.*'))
    level_invalid = glob.glob(os.path.join(level_invalid_path,'*-' + file_id + '.*'))
    for filename in level_prods + level_ql + level_logs + level_invalid:
        try:
            logging.info('Removing previous file: {}'.format(filename))
            os.remove(filename)
        except:
            pass

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
    
filename_field_sep = '-' 
delimiter = '|'
cor_ext = '.txt.gz'
level = 'level1c'
level_prev = 'level1b'
header = True 
wmode = 'w'
    
release_path = os.path.join(params.data_path,params.release,params.source)
release_id = filename_field_sep.join([params.release,params.update ]) 
fileID = filename_field_sep.join([str(params.year),str(params.month).zfill(2),release_id ])
fileID_date = filename_field_sep.join([str(params.year),str(params.month)])

cor_id_path = os.path.join(release_path,level_prev,'linkage')
prev_level_path = os.path.join(release_path,level_prev,params.sid_dck)  
level_path = os.path.join(release_path,level,params.sid_dck)
level_ql_path = os.path.join(release_path,level,'quicklooks',params.sid_dck)
level_log_path = os.path.join(release_path,level,'log',params.sid_dck)
level_invalid_path = os.path.join(release_path,level,'invalid',params.sid_dck)

data_paths = [prev_level_path, level_path, level_ql_path, level_log_path, level_invalid_path]
if any([ not os.path.isdir(x) for x in data_paths ]):
    logging.error('Could not find data paths: {}'.format(','.join([ x for x in data_paths if not os.path.isdir(x)])))
    sys.exit(1)

prev_level_filename = os.path.join(prev_level_path, 'header-' + fileID + '.psv')
if not os.path.isfile(prev_level_filename):
    logging.error('L1b header file not found: {}'.format(prev_level_filename))
    sys.exit(1)
 
# Clean previous L1c products and side files ----------------------------------
clean_level(fileID)
validation_dict = { table:{} for table in cdm.properties.cdm_tables}

# DO THE DATA PROCESSING ------------------------------------------------------
# -----------------------------------------------------------------------------

validated = ['report_timestamp','primary_station_id']
history_tstmp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
history_explain = 'Performed report_timestamp (date_time) and primary_station_id validation'
cdm_tables = cdm.lib.tables.tables_hdlr.load_tables()

# 1. READ THE DATA-------------------------------------------------------------
# Read the header table and init the mask to True
table = 'header'
table_df = pd.DataFrame()
# On reading 'header' read null as NaN so that we can validate null ids as NaN easily
table_df = cdm.read_tables(prev_level_path,fileID,cdm_subset=[table],na_values='null')
if len(table_df) == 0:
    logging.error('Empty or non-existing header table')
    sys.exit(1)
    
table_df.set_index('report_id', inplace = True, drop = False)

# Initialize mask
mask_df = pd.DataFrame(index = table_df.index,columns = validated + ['all'])
mask_df[validated] = True

# 2. VALIDATE THE FIELDS-------------------------------------------------------
# 2.1. Validate datetime
field = 'report_timestamp'
mask_df[field] = pd.to_datetime(table_df[field],errors='coerce').notna()

# 2.2. Validate primary_station_id
field = 'primary_station_id'
validation_dict['id_validation_rules'] = {}

# First get callsigns:
logging.info('Applying callsign id validation')
callsigns = table_df['primary_station_id_scheme'].isin(['5']) & table_df['platform_type'].isin(['2','33'])
nocallsigns = ~callsigns
relist = ['^([0-9]{1}[A-Z]{1}|^[A-Z]{1}[0-9]{1}|^[A-Z]{2})[A-Z0-9]{1,}$','^[0-9]{5}$']
callre = re.compile('|'.join(relist))
mask_df.loc[callsigns,field] = table_df.loc[callsigns,field].str.match(callre,na = True)

# Then the rest according to general validation rules
logging.info('Applying general id validation')
table_df.columns = [ ('header',x) for x in table_df.columns ]
mask_df.loc[nocallsigns,field]  = validate_id.validate(table_df.loc[nocallsigns],'cdm',params.sid_dck.split('-')[1], blank=True) 
table_df.columns = [ x[1] for x in table_df.columns ]

# And now set back to True all that the linkage provided
logging.info('Restoring pre-corrected ids')
idcor_file = os.path.join(cor_id_path, '_'.join(['id',params.release,params.update]), fileID_date + cor_ext)
if not os.path.isfile(idcor_file):
    logging.error('id correction file {} not found'.format(idcor_file))
    sys.exit(1)
columns = ['report_id','applied']
idcor_df =  pd.read_csv(idcor_file, delimiter = delimiter, dtype = 'object',
                           header = None, usecols=[0,2], names = columns,
                           quotechar=None,quoting=3,index_col = ['report_id'])

try:
    idcor_df = idcor_df.loc[table_df.index]
    idcor_df = idcor_df.loc[idcor_df['applied'] == '1' ]
    mask_df.loc[idcor_df.index,field] = True
    validation_dict['id_validation_rules']['idcorrected'] = len(np.where(idcor_df)[0])
except:
    logging.warning(logging.warning('No ID corrections applied'))
    validation_dict['id_validation_rules']['idcorrected'] = 0

validation_dict['id_validation_rules']['callsign'] = len(np.where(callsigns)[0])
validation_dict['id_validation_rules']['noncallsign'] = len(np.where(~callsigns)[0])

# 3. OUTPUT INVALID REPORTS - HEADER ------------------------------------------
cdm_columns = cdm_tables.get(table).keys()
for field in validated:
    if False in mask_df[field].value_counts().index:
        idata_filename = os.path.join(level_invalid_path,filename_field_sep.join(['header',fileID,field]) + '.psv')
        table_df[~mask_df[field]].to_csv(idata_filename, index = False, sep = delimiter, columns = cdm_columns
                 ,header = header, mode = wmode, na_rep = 'null')


# 4. REPORT INVALIDS PER FIELD  -----------------------------------------------    
# Now clean, keep only all valid:
mask_df['all'] = mask_df.all(axis=1) 

# Report invalids
validation_dict['invalid'] = {} 
validation_dict['invalid']['total'] = len(table_df[~mask_df['all']])
for field in validated:
    validation_dict['invalid'][field] = len(mask_df[field].loc[~mask_df[field]])

# 5. CLEAN AND OUTPUT TABLES  -------------------------------------------------
# Now process tables and log final numbers and some specifics in header table
# First header table, already open
logging.info('Cleaning table header') 
process_table(table_df,table)
obs_tables = [ x for x in cdm_tables.keys() if x != 'header' ]
for table in obs_tables:
    logging.info('Cleaning table {}'.format(table))   
    process_table(table,table)
    
logging.info('Saving json quicklook')
L1b_io_filename = os.path.join(level_ql_path,fileID + '.json')
with open(L1b_io_filename,'w') as fileObj:
    simplejson.dump({'-'.join([params.year,params.month]):validation_dict},fileObj,
                     default = date_handler,indent=4,ignore_nan=True)

