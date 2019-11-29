#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:24:10 2019

See IMPORTANT NOTE!!!!

Script to generate the C3S CDM Marine level1c data: add external MD (pub47...):

    - Read header table and MD and see if there is anything to merge
    
    - Map MD to CDM with function map_to_cdm()
    
    - Merge mapped MD with CDM tables and save to file with function process_table()
    (if nothing to merge, just save the file to level1d...)
    
    - read metadata (currently only pub47, should be easily parameterizable,
    well, not the mappings...... maybe should use cdm module in future, that's its place!)
    - merge by primary_station_id
    - log, per table, total number of records and those with MD added/updated

The processing unit is the source-deck monthly set of CDM tables.

Outputs data to /<data_path>/<release>/<source>/level1d/<sid-dck>/table[i]-fileID.psv
Outputs quicklook info to:  /<data_path>/<release>/<source>/level1d/quicklooks/<sid-dck>/fileID.json
where fileID is yyyy-mm-release_tag-update_tag

Before processing starts:
    - checks the existence of all io subdirectories in level1c|d -> exits if fails
    - checks the existence of the source table to be converted (header only) -> exits if fails
    - checks the existence of the monthly MD file -> exits if fails. See IMPORTANT NOTE!!!!
    - removes all level1d products on input file resulting from previous runs



Inargs:
------
data_path: data release parent path (i.e./gws/nopw/c3s311_lot2/data/marine)
sid_dck: source-deck partition (sss-ddd)
year: data file year (yyyy)
month: data file month (mm)
release: release identifier
update: release update identifier
source: source dataset identifier

On input data:
-------------
If the pre-processing of the MD changes, then how we map the MD in map_to_cdm()
 changes also. The mappings there as for MD pre-processing in Autumn2019

pub47 monthly files assumed to have 1 hdr line (first) with column names
pub47 monthly files with FS=';'
pub47 field names assumed: call;record;name;freq;vsslM;vssl;automation;rcnty;
                           valid_from;valid_to;uid;thmH1;platH;brmH1;
                           anmH;anHL1;wwH;sstD1;th1;hy1;st1;bm1;an1


IMPORTANT NOTE:
--------------
DIRTY LAST MINUTE HARDCODE FOR RELEASE1 (AUTUMN 2019):
    
    NO MD EXPECTED AFTER 2010 OR BEFORE 1956: 
    -> DO NOT FAIL IF NO MD: JUST CONTINUE WITH NO MERGING
    

Dev notes:
---------

1) md param mainly to provide in the future for MD sources other than pub47, and maybe parameterize this...
        
2) Mapping of MD is performed here in a quite dirty way, using, on top of it, a dict
to make it usable for eventual future new MD sources, that anyway would probably fail to do the job!!!!
A new funtion like the current map_to_cdm() would be needed for every new MD source: if any!

So basically: add this mappings to the CDM module: that's what it is meant for:
    1. Read MD file to DF, using column names and datatypes as reflected in the mapping set up in CDM module
    2. Map MD to CDM with cdm module
    3. Then merge to the CDM obs tables: probably as we already do here with process_table()
.....

@author: iregon
"""
import sys
import os
import simplejson
import datetime
import cdm
from collections import Counter
import glob
import logging
import pandas as pd
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

def join_cols(df,cols):
    s = df[cols[0]]
    if len(cols) > 1:
        for c in cols[1:]:
            s = s + '-' + df[c]
    return s

def select_cols(df,cols):
    c = cols.copy()
    c.reverse()
    s = df[c[0]].copy()
    if len(c)> 1:
        for ci in c[1:]:
            s.update(df[ci])
    return s

def map_to_cdm():
    meta_cdm_columns = [ ('header',x) for x in metadata.get(md).get('header') ]
    for obs_table in obs_tables:
        meta_cdm_columns.extend([ (obs_table,x) for x in metadata.get(md).get('observations') ])

    meta_cdm = pd.DataFrame(index = meta_df.index, columns = meta_cdm_columns)
    # First the direct mappings to the header table elements
    table = 'header'
    meta_cdm[[ x for x in meta_cdm if x[0] == table ]] = meta_df[['name','vssl','call','record','freq']]
    # Now the table-wise, element wise mappings to the observations tables
    field ='sensor_automation_status'
    meta_cdm.loc[:,[ (x,field) for x in obs_tables ]] = meta_df[['automation']]

    field = 'sensor_id'
    for table in  obs_tables:
        meta_field = metadata['pub47']['sensor_id'].get(table)
        meta_cdm[(table,field)] = join_cols(meta_df,['uid','record',meta_field])

    field = 'z_coordinate'
    for table in obs_tables:
        meta_fields = metadata['pub47']['heights'].get(table)
        meta_cdm[(table,field)] = select_cols(meta_df,meta_fields)
        if table == 'observations-sst':
            meta_cdm[(table,field)] = '-' +  meta_cdm[(table,field)]   
        meta_cdm[(table,'observation_height_above_station_surface')] = meta_cdm[(table,field)]
        
    return meta_cdm


def process_table(table_df,table_name):
    logging.info('Processing table {}'.format(table_name))
    if isinstance(table_df,str):
        # Assume 'header' and in a DF in table_df otherwise
        # Open table and reindex
        table_df = pd.DataFrame()
        table_df = cdm.read_tables(prev_level_path,fileID,cdm_subset=[table_name])
        if table_df is None or len(table_df) == 0:
            logging.warning('Empty or non existing table {}'.format(table_name))
            return
        table_df.set_index('report_id',inplace=True,drop=False)
        # by this point, header_df has its index set to report_id, hopefully ;)
        table_df['primary_station_id'] = header_df['primary_station_id'].loc[table_df.index]

    meta_dict[table_name] = {'total':len(table_df),'updated':0}
    if merge:
        meta_dict[table_name] = {'total':len(table_df),'updated':0}
        table_df.set_index('primary_station_id',drop=False,inplace=True)

        meta_table = meta_cdm[[ x for x in meta_cdm if x[0] == table_name ]]
        meta_table.columns = [ x[1] for x in meta_table ]
        if table_name != 'header':
            meta_table['primary_station_id'] = meta_cdm[('header','primary_station_id')]
        meta_table.set_index('primary_station_id',drop=False,inplace=True)
        table_df.update(meta_table)

        updated_locs =  [ x for x in table_df.index if x in meta_table.index ]
        meta_dict[table_name]['updated'] = len(updated_locs)

        if table_name == 'header':
            missing_ids = [ x for x in table_df.index if x not in meta_table.index ]
            if len(missing_ids)>0:
                meta_dict['non ' + md + ' ids'] = {k:v for k,v in Counter(missing_ids).items()}
            history_add = ';{0}. {1}'.format(history_tstmp,history_explain)
            locs = table_df['primary_station_id'].isin(updated_locs)
            table_df['history'].loc[locs] = table_df['history'].loc[locs] + history_add

    cdm_columns = cdm_tables.get(table_name).keys()
    odata_filename = os.path.join(level_path,filename_field_sep.join([table_name,fileID]) + '.psv')
    table_df.to_csv(odata_filename, index = False, sep = delimiter, columns = cdm_columns
                 ,header = header, mode = wmode, na_rep = 'null')

    return

def clean_level(file_id):
    level_prods = glob.glob(os.path.join(level_path,'*-' + file_id + '.psv'))
    level_logs = glob.glob(os.path.join(level_log_path, file_id + '.*'))
    level_ql = glob.glob(os.path.join(level_ql_path, file_id + '.*'))
    for filename in level_prods + level_ql + level_logs:
        try:
            logging.info('Removing previous file: {}'.format(filename))
            os.remove(filename)
        except:
            pass

# END FUNCTIONS ---------------------------------------------------------------
            
# MD parameterization, this should go to outer file ---------------------------
metadata = {}
metadata['pub47'] = {}
metadata['pub47']['history'] = 'WMO Publication 47 metadata added'
metadata['pub47']['header'] = ['station_name','platform_sub_type','primary_station_id','station_record_number','report_duration']
metadata['pub47']['observations'] = ['z_coordinate','observation_height_above_station_surface','sensor_id','sensor_automation_status']
metadata['pub47']['heights'] = {
        'observations-at':['thmH1','platH','brmH1'],
        'observations-dpt':['thmH1','brmH1','platH'],
        'observations-wbt':['thmH1','brmH1','platH'],
        'observations-sst':['sstD1'],
        'observations-slp':['brmH1','platH'],
        'observations-wd':['anmH','anHL1','platH'],
        'observations-ws':['anmH','anHL1','platH']
        }
metadata['pub47']['sensor_id'] = {
        'observations-at':'th1',
        'observations-dpt':'hy1',
        'observations-wbt':'hy1',
        'observations-sst':'st1',
        'observations-slp':'bm1',
        'observations-wd':'an1',
        'observations-ws':'an1'
        }

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
md_delimiter = '|'
level = 'level1d'
level_prev = 'level1c'
header = True
wmode = 'w'

release_path = os.path.join(params.data_path,params.release,params.source)
release_id = filename_field_sep.join([params.release,params.update ])
fileID = filename_field_sep.join([str(params.year),str(params.month).zfill(2),release_id ])
fileID_date = filename_field_sep.join([str(params.year),str(params.month)])

prev_level_path = os.path.join(release_path,level_prev,params.sid_dck)
level_path = os.path.join(release_path,level,params.sid_dck)
level_ql_path = os.path.join(release_path,level,'quicklooks',params.sid_dck)
level_log_path = os.path.join(release_path,level,'log',params.sid_dck)

md_path = os.path.join(params.data_path,params.release,'Pub47')

data_paths = [prev_level_path, level_path, level_ql_path, level_log_path, md_path ]
if any([ not os.path.isdir(x) for x in data_paths ]):
    logging.error('Could not find data paths: {}'.format(','.join([ x for x in data_paths if not os.path.isdir(x)])))
    sys.exit(1)

prev_level_filename = os.path.join(prev_level_path, 'header-' + fileID + '.psv')
if not os.path.isfile(prev_level_filename):
    logging.error('L1c header file not found: {}'.format(prev_level_filename))
    sys.exit(1)

metadata_filename = os.path.join(md_path, params.year + filename_field_sep + params.month + '-01.csv')
md_avail = True
if not os.path.isfile(metadata_filename):
    if int(params.year) > 2010 or int(params.year) < 1956:
        md_avail = False
        logging.warning('Metadata not available after 2010. Creating level1d product with no merging')
    else:
        logging.error('Metadata file not found: {}'.format(metadata_filename))
        sys.exit(1)
        
# Clean previous L1a products and side files ----------------------------------
clean_level(fileID)
meta_dict = {}

# DO THE DATA PROCESSING ------------------------------------------------------
# -----------------------------------------------------------------------------
md = 'pub47'
history_tstmp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
history_explain = metadata.get(md).get('history')
cdm_tables = cdm.lib.tables.tables_hdlr.load_tables()
obs_tables = [ x for x in cdm_tables.keys() if x != 'header' ]

# 1. SEE STATION ID's FROM BOTH DATA STREAMS AND SEE IF THERE'S ANYTHING TO
# MERGE AT ALL
# Read the header table
table = 'header'
header_df = pd.DataFrame()
header_df = cdm.read_tables(prev_level_path,fileID,cdm_subset=[table],na_values='null')
if len(header_df) == 0:
    logging.error('Empty or non-existing header table')
    sys.exit(1)

# Read the metadona
if md_avail:
    meta_df = pd.DataFrame()
    meta_df = pd.read_csv(metadata_filename,delimiter = md_delimiter, dtype = 'object',
                               header = 0, na_values='MSNG')
    if len(meta_df) == 0:
        logging.error('Empty or non-existing metadata file')
        sys.exit(1)

# See if there's anything to do
header_df.set_index('primary_station_id',drop = False, inplace = True)
merge = True if md_avail else False
if md_avail:
    meta_df = meta_df.loc[meta_df['call'].isin(header_df['primary_station_id'])]
    if len(meta_df) == 0:
        logging.warning('No metadata to merge in file')
        merge = False

# 2. MAP PUB47 MD TO CDM FIELDS -----------------------------------------------
if merge:
    logging.info('Mapping metadata to CDM')
    meta_cdm = map_to_cdm()

# 3. UPDATE CDM WITH PUB47 OR JUST COPY PREV LEVEL TO CURRENT -----------------
# This is only valid for the header
table =  'header'
process_table(header_df,table)

header_df.set_index('report_id',inplace=True,drop=False)
# for obs
for table in obs_tables:
    process_table(table,table)

# 4. SAVE QUICKLOOK -----------------------------------------------------------
logging.info('Saving json quicklook')
level_io_filename = os.path.join(level_ql_path,fileID + '.json')
with open(level_io_filename,'w') as fileObj:
    simplejson.dump({'-'.join([params.year,params.month]):meta_dict},fileObj,
                     default = date_handler,indent=4,ignore_nan=True)

