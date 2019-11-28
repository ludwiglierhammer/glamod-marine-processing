#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:24:10 2019

Script to generate the C3S CDM Marine level1a data. 

    - Reads source data (and supp if avail) file with modeule mdf_reader. This 
    includes a data model validation mask.
    - fixes known PT type errors in source dataset with module metmetpy
    - selects data reports according to filtering requests
    - rejects data reports not validiting against its data model
    - maps to the C3S CDM header and observations tables if there is data left
    after cleaning (table[i].psv CDM table-like files)

The processing unit is the source-deck monthly file.

Outputs data to /<data_path>/<release>/<source>/level1a/<sid-dck>/table[i]-fileID.psv
Outputs invalid data to /<data_path>/<release>/<source>/level1a/invalid/<sid-dck>/fileID-data|mask.psv
Outputs exluded data to /<data_path>/<release>/<source>/level1a/excluded/<sid-dck>/fileID-<filterfield>.psv
Outputs quicklook info to:  /<data_path>/<release>/<source>/level1a/quicklooks/<sid-dck>/fileID.json
Outputs quicklook info to:  /<data_path>/<release>/<source>/level1a/quicklooks/<sid-dck>/table[i]-fileID.nc

where fileID is year-month-release-update

Before processing starts:
    - checks the existence of all output subdirectories in level1a -> exits if fails
    - checks the existence of the source file to be converted -> exits if fails
    - removes all level1a products on input file resulting from previous runs

On input data:
-------------
Records of input data (main body and optionally, supplemental data)
assumed to be in the sid-deck monthly partitions which imply:
    - data for same month-year period
    - body/main data from a unique data model
    - supplemental data (optionally) from a unique data model
    

Inargs:
------

data_path: data release parent path (i.e./gws/nopw/c3s311_lot2/data/marine)
sid_dck: source-deck partition (sss-ddd)
year: data file year (yyyy)
month: data file month (mm)
release: release identifier
update: release update identifier
source: source dataset identifier
configfile: path to configuration file with processing options

configfile:
----------
To specify processing options that may be shared in different processing
settings:
    - main data model
    - supplemental data model
    - processing options: supplemental replacements,
    record selection/filtering by field (i.e. PT....)

dev notes:
---------

1) Currently still slightly tunned for ICOADS/IMMA only:
    - level0 data sought before beginning is *.imma

2) Chunksize is hardcoded here to 200000

3) The way the invalid data tracking is done is awfull, partly because of the
chunking....find cleaner way to do it

4) Also there is an error in the binning of the numeric invalids. This was
also found and solved in another level (see L1b_merge.py). Have to incorporate this here.
 
5) Initially, file permission where changed to rwxrwxr-- to all output at
the end of the script with the lines below, however, it seemed that a user not
being the user that initially created the file could not do this...?? so in
the end it was decided to set umask 002 to the ./bashrc file

    out_paths = [L1a_path,L1a_ql_path,L1a_excluded_path,L1a_invalid_path]
    logging.info('Changing output file permissions')
    for out_path in out_paths:
        outfiles = glob.glob(os.path.join(out_path,'*' + L1a_id + '*'))
        for outfile in outfiles:
            os.chmod(outfile,0o664)
        
.....

@author: iregon
"""
import sys
import os
import json
from io import StringIO
import simplejson
import datetime
import mdf_reader
import cdm
import metmetpy
from pandas_operations import select,inspect
from pandas_operations.common import TextParser_hdlr
import glob
import logging
import pandas as pd
import numpy as np
import copy
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
        self.configfile =  inargs[8]
        try:
            with open(self.configfile) as fileObj:
                config = json.load(fileObj)
            for k,v in config.items():
                setattr(self, k, v)
            self.flag = True
        except Exception:
            logging.error('Parsing configuration from file :{}'.format(self.configfile), exc_info=True)
            self.flag = False

# This is for json to handle dates
date_handler = lambda obj: (
    obj.isoformat()
    if isinstance(obj, (datetime.datetime, datetime.date))
    else None
)

def clean_L1a(L1a_id):
    L1a_prods = glob.glob(os.path.join(L1a_path,'*-' + L1a_id + '.psv'))
    L1a_prods_idate = glob.glob(os.path.join(L1a_path,'*' + '-'.join([str(params.year),str(params.month).zfill(2)]) + '.psv'))
    L1a_ql = glob.glob(os.path.join(L1a_ql_path, L1a_id + '.*'))
    L1a_excluded = glob.glob(os.path.join(L1a_excluded_path, L1a_id + '-*.psv'))
    L1a_invalid = glob.glob(os.path.join(L1a_invalid_path, L1a_id + '-*.psv'))
    for filename in L1a_prods + L1a_prods_idate + L1a_ql + L1a_excluded + L1a_invalid:
        try:
            logging.info('Removing previous file: {}'.format(filename))
            os.remove(filename)
        except:
            pass

# MAIN ------------------------------------------------------------------------

# PROCESS INPUT AND MAKE SOME CHECKS ------------------------------------------
logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)
if len(sys.argv)>1:
    logging.info('Reading command line arguments')
    args = sys.argv
else:
    logging.error('Need arguments to run!')
    sys.exit(1)

params = script_setup(args)

if not params.flag:
    logging.error('Error parsing initial configuration')
    sys.exit(1)
    
release_path = os.path.join(params.data_path,params.release,params.source)

filename_field_sep = '-'    
L0_path = os.path.join(release_path,'level0',params.sid_dck)   
L1a_path = os.path.join(release_path,'level1a',params.sid_dck)
L1a_ql_path = os.path.join(release_path,'level1a','quicklooks',params.sid_dck)
L1a_excluded_path = os.path.join(release_path,'level1a','excluded',params.sid_dck)
L1a_invalid_path = os.path.join(release_path,'level1a','invalid',params.sid_dck)

data_paths = [L0_path, L1a_path, L1a_ql_path, L1a_excluded_path, L1a_invalid_path]
if any([ not os.path.isdir(x) for x in data_paths ]):
    logging.error('Could not find data paths: '.format(','.join([ x for x in data_paths if not os.path.isdir(x)])))

L0_filename = os.path.join(L0_path,filename_field_sep.join([params.year,params.month]) + '.imma')
if not os.path.isfile(L0_filename):
    logging.error('L0 file not found: {}'.format(L0_filename))
    
release_id = filename_field_sep.join([params.release,params.update ])   
L1a_id = filename_field_sep.join([str(params.year),str(params.month).zfill(2),release_id ])

# CLEAN PREVIOUS L1A PRODUCTS AND SIDE FILES ----------------------------------
clean_L1a(L1a_id)

# DO THE DATA PROCESSING ------------------------------------------------------
data_model = params.main_data_model
io_dict = {}

#1. Read input file to dataframe
logging.info('Reading source data')

process_kwargs = {'data_model':params.main_data_model,
                  'sections':params.read_sections,
                  'chunksize':200000}

if hasattr(params,'supp_section'):
    if not hasattr(params,'supp_data_model'):
        logging.error('Data model for supplemental section {} not provided'.format(params.supp_section))
    else:
        process_kwargs.update({'supp_section':params.supp_section})
        process_kwargs.update({'supp_model':params.supp_data_model})
        
data_in = mdf_reader.read(L0_filename, **process_kwargs)

io_dict['read'] = {'total':inspect.get_length(data_in['data'])}

# 2. PT fixing, filtering and invalid rejection
# 2.1. Fix platform type
logging.info('Fixing platform type')
data_in['data'] = metmetpy.correct_pt.correct(data_in['data'],data_model,params.dck)

# 2.2. Apply record selection (filter by) criteria: PT types.....
if hasattr(params, 'filter_by'):
    logging.info('Applying selection filters')
    io_dict['not_selected'] = {}
    data_excluded = {}
    data_excluded['atts'] = data_in['atts'].copy()
    data_excluded['data'] = {}
    # 3.1. Select by filter_by options
    for k,v in params.filter_by.items():
        io_dict['not_selected'][k] = {}
        logging.info('Selecting {0} values: {1}'.format(k,','.join(v.get('values'))))
        col = (v.get('section'),v.get('element')) if v.get('section') else v.get('element')
        values = v.get('values')
        selection={col:values}
        data_in['data'],data_excluded['data'][k],index = select.select_from_list(data_in['data'],selection,out_rejected = True,in_index = True)
        data_in['valid_mask']= select.select_from_index(data_in['valid_mask'],index)
        io_dict['not_selected'][k]['total'] = inspect.get_length(data_excluded['data'][k])
        if io_dict['not_selected'][k]['total'] > 0:
            if data_in['atts'][col]['column_type'] in ['str','object','key']:
                io_dict['not_selected'][k].update(inspect.count_by_cat(data_excluded['data'][k],col))
    io_dict['not_selected']['total'] = sum([ v.get('total') for k,v in io_dict['not_selected'].items()])

io_dict['pre_selected'] = {'total':inspect.get_length(data_in['data'])}    

# 2.3. Keep track of invalid data 
# First create a global mask and count failure occurrences
newmask_buffer = StringIO()
logging.info('Removing invalid data')
for data,mask in zip(data_in['data'],data_in['valid_mask']):
    # 2.3.1. Global mask
    mask['global_mask'] = mask.all(axis=1)
    mask.to_csv(newmask_buffer,header = False, mode = 'a', encoding = 'utf-8',index = False)
    # 2.3.2. Invalid reports counts and values
    # Initialize counters if first chunk
    masked_columns = [ x for x in mask if not all(mask[x].isna()) and x!=('global_mask','') ]
    if not io_dict.get('invalid'):
        io_dict['invalid'] = {".".join(k):{'total':0,'values':[]} for k in masked_columns}
    for col in masked_columns:
        k = ".".join(col)
        io_dict['invalid'][k]['total'] += len(mask[col].loc[~mask[col]])
        if col in data: # cause some masks are not in data (datetime....)
            io_dict['invalid'][k]['values'].extend(data[col].loc[~mask[col]].values)

newmask_buffer.seek(0)   
chunksize = None if isinstance(data_in['valid_mask'],pd.DataFrame) else data_in['valid_mask'].orig_options['chunksize']
data_in['valid_mask'] = pd.read_csv(newmask_buffer,names = [ x for x in mask ], chunksize = chunksize)    
data_in['data'] = TextParser_hdlr.restore(data_in['data'])
# Now see what fails
for col in masked_columns:
    object_types = ['str','object','key']
    numeric_types = ['int8','int16','int32','int64','uint8','uint16','uint32','uint64','float16','float32','float64']
    k = '.'.join(col)
    if io_dict['invalid'][k]['total'] > 0:
        if data_in['atts'].get(col,{}).get('column_type') in object_types:
            ivalues = list(set(io_dict['invalid'][k]['values']))
            # This is because sorting fails on strings if nan
            if np.nan in ivalues:
                ivalues.remove(np.nan)
                ivalues.sort()
                ivalues.append(np.nan)
            else:
                ivalues.sort()
            io_dict['invalid'][k].update({i:io_dict['invalid'][k]['values'].count(i) for i in ivalues})
            sush = io_dict['invalid'][k].pop('values',None)
        elif data_in['atts'].get(col,{}).get('column_type') in numeric_types:
            values = io_dict['invalid'][k]['values']
            values = np.array(values)[~np.isnan(np.array(values))]
            if len(values>0):
                [counts,edges] = np.histogram(values)
                # Following binning approach only if at most 1 sign digit!
                bins = [ '-'.join(["{:.1f}".format(edges[i]),"{:.1f}".format(edges[i+1])]) for i in range(0,len(edges)-1)]
                io_dict['invalid'][k].update({b:counts for b,counts in zip(bins,counts)})
            else:
                io_dict['invalid'][k].update({'nan?':len(io_dict['invalid'][k]['values'])})
            sush = io_dict['invalid'][k].pop('values',None)
    else:
        sush = io_dict['invalid'].pop(k,None)

# 2.4. Discard invalid data. 
data_invalid = {}
data_invalid['atts'] = data_in['atts'].copy()
col = 'global_mask'            
data_in['data'],data_invalid['data'] = select.select_true(data_in['data'],data_in['valid_mask'],col,out_rejected = True)
data_in['valid_mask'],data_invalid['valid_mask'] = select.select_true(data_in['valid_mask'],data_in['valid_mask'],col,out_rejected = True)
            
io_dict['invalid']['total'] = inspect.get_length(data_invalid['data'])         
io_dict['processed'] = {'total':inspect.get_length(data_in['data'])}

process = True
if io_dict['processed']['total'] == 0:
    process = False
    logging.warning('No data to map to CDM after selection and cleaning')

# 3. Map to common data model and output files
if process:
    logging.info('Mapping to CDM')
    tables = ['header','observations-at','observations-sst','observations-dpt',
                  'observations-wbt','observations-wd','observations-ws','observations-slp']
    obs_tables = tables[1:]
    io_dict.update({table:{} for table in tables})
    mapping = params.cdm_map
    cdm_tables = cdm.map_model(mapping, data_in['data'], data_in['atts'],
                               log_level = 'INFO')
    
    logging.info('Printing tables to psv files')
    cdm.cdm_to_ascii(cdm_tables,log_level ='DEBUG',
                     out_dir = L1a_path, suffix = L1a_id, prefix = None)
        
    for table in tables:
        io_dict[table]['total'] = inspect.get_length(cdm_tables[table]['data'])
        
    # Do the quick stats and save ql ----------------------------------------------
    logging.info('Computing gridded stats')
    cdm.gridded_stats.from_cdm_monthly(L1a_path, cdm_id = L1a_id, region = 'Global', 
                      resolution = 'lo_res', nc_dir = L1a_ql_path, qc=False)

io_dict['date processed'] = datetime.datetime.now()
logging.info('Saving json quicklook')
L1a_io_filename = os.path.join(L1a_ql_path,L1a_id + '.json')
with open(L1a_io_filename,'w') as fileObj:
    simplejson.dump({'-'.join([params.year,params.month]):io_dict},fileObj,
                     default = date_handler,indent=4,ignore_nan=True)
    
# Output exluded and invalid ---------------------------------------------
def write_out_junk(dataObj,filename):
    v = [dataObj] if not process_kwargs.get('chunksize') else dataObj
    c = 0
    for df in v:
        wmode = 'a' if c > 0 else 'w'
        header = False if c > 0 else True
        df.to_csv(filename, sep = '|', mode = wmode, header = header)
        c += 1    
    
if hasattr(params, 'filter_by'):
    for k,v in data_excluded['data'].items():
        if inspect.get_length(data_excluded['data'][k]) > 0:
            excluded_filename = os.path.join(L1a_excluded_path,L1a_id + filename_field_sep + k + '.psv')  
            logging.info('Writing {0} excluded data to file {1}'.format(k,excluded_filename))
            write_out_junk(v,excluded_filename)

if inspect.get_length(data_invalid['data']) > 0:
    invalid_data_filename = os.path.join(L1a_invalid_path,L1a_id + filename_field_sep + 'data.psv')
    invalid_mask_filename = os.path.join(L1a_invalid_path,L1a_id + filename_field_sep + 'mask.psv')
    logging.info('Writing invalid data to file {}'.format(invalid_data_filename))
    write_out_junk(data_invalid['data'],invalid_data_filename)
    logging.info('Writing invalid data mask to file {}'.format(invalid_mask_filename))
    write_out_junk(data_invalid['valid_mask'],invalid_mask_filename)

