#!/usr/bin/env python3
#
#  Needs to run with py env2: bwcause of pandas to_parquet (different to dask to parquet!)
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 09:24:24 2020

RUN WITH ENV2!!!!

@author: iregon
"""
import os
import sys
import glob
import json
import pandas as pd
import logging

from dask import dataframe as dd
import dask.diagnostics as diag
import datashader as ds
import xarray as xr
import datetime
from dateutil import rrule

from data_summaries import properties
from data_summaries import query_cdm


LEN_DD = 10000 # DF LEN TO SWAP TO DASK-PARQUET AGGREGATION
# FUNCTIONS -------------------------------------------------------------------
def bounds(x_range, y_range):
    return dict(x_range=x_range, y_range=y_range)

def create_canvas(bbox,degree_factor):
    plot_width = int(abs(bbox[0][0]-bbox[0][1])*degree_factor)
    plot_height = int(abs(bbox[1][0]-bbox[1][1])*degree_factor)    
    return ds.Canvas(plot_width=plot_width, plot_height=plot_height, **bounds(*bbox))

# END FUNCTIONS ---------------------------------------------------------------
        
# MAIN ------------------------------------------------------------------------    
logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)

table = sys.argv[1]
config_file = sys.argv[2]

with open(config_file,'r') as fO:
    config = json.load(fO)

# KWARGS FOR CDM FILE QUERY----------------------------------------------------
kwargs = {}
kwargs['dir_data'] = config['dir_data']
kwargs['cdm_id'] = '*'
kwargs['columns'] = ['latitude','longitude','date_time','observation_value']
kwargs['filter_by_values'] = config[table]['filter_by_values']
for kv in list(kwargs.get('filter_by_values').items()):
                    kwargs['filter_by_values'][(kv[0].split('.')[0],kv[0].split('.')[1])] = kwargs['filter_by_values'].pop(kv[0])

# CREATE CANVAS FROM PARAMS ---------------------------------------------------
region = config['region']
resolution = config['resolution']
canvas = create_canvas(properties.REGIONS.get(region),properties.DEGREE_FACTOR_RESOLUTION.get(resolution))

# CREATE THE MONTHLY STATS ON THE DF PARTITIONS -------------------------------
nreports_list = []
mean_list = []
start = datetime.datetime(config['start'],1,1)
stop = datetime.datetime(config['stop'],12,31)
for dt in rrule.rrule(rrule.MONTHLY, dtstart=start, until=stop):
    date_file = dt.strftime('%Y-%m')
    parq_path = os.path.join(config['dir_out'],'-'.join([date_file,table,'.data.parq.tmp']))
    files_list = glob.glob(os.path.join(config['dir_data'],'*','-'.join([table,date_file]) + '*.psv' ))
    if len(files_list) == 0:
        logging.warning('NO DATA FILES FOR TIME PARTITION {}'.format(date_file))
        continue

    sid_dck_list = [ os.path.basename(os.path.dirname(x)) for x in files_list ]
    cdm_table_ym = pd.DataFrame()
    logging.info('PROCESSING TIME PARTITION: {0}. Aggregating {1} sources'.format(date_file,str(len(sid_dck_list))))
    for sid_dck in sid_dck_list:
        cdm_table = query_cdm.query_monthly_table(sid_dck, table, dt.year, dt.month, **kwargs)
        cdm_table.dropna(inplace = True)
        cdm_table_ym = pd.concat([cdm_table_ym,cdm_table], sort = False)

    len_table_ym = len(cdm_table_ym)
    logging.info('DF LEN: {}'.format(len(cdm_table_ym)))
    # SAVE TO PARQUET AND READ DF BACK FROM THAT TO ENHANCE PERFORMANCE
    # CHECK HERE NUMBER OF RECORDS AFTER AND BEFORE SAVING, ETC....
    if len_table_ym > LEN_DD:
        logging.info('Time partition to parquet')
        with diag.ProgressBar(), diag.Profiler() as prof, diag.ResourceProfiler(0.5) as rprof:
            #append = False if i == 0 else True
            #cdm_table.to_parquet(parq_path, engine = 'pyarrow',mode='a')#, compression = 'gzip', append = append)
            #cdm_table_ym.to_parquet(parq_path, engine = 'fastparquet', compression = 'gzip', append = append)
            cdm_table_ym.to_parquet(parq_path, engine = 'fastparquet', compression = 'gzip',append = False)  
        del cdm_table_ym
        
        logging.info('Time parition from parquet')
        cdm_table_ym = dd.read_parquet(parq_path)
    logging.info('Canvas aggregation')
    nreports_arr = canvas.points(cdm_table_ym,'longitude','latitude',ds.count('observation_value')).assign_coords(time=dt).rename('counts')
    mean_arr = canvas.points(cdm_table_ym,'longitude','latitude',ds.mean('observation_value')).assign_coords(time=dt).rename('mean')
    nreports_list.append(nreports_arr)
    logging.info(nreports_arr.max())
    mean_list.append(mean_arr)
    logging.info(mean_arr.max())

#    Now this seems different with pandas to parquet, is it the engine choice?
#    shutil.rm(parq_path)
    if len_table_ym > LEN_DD:
        os.remove(parq_path)

    
nreports_agg = xr.concat(nreports_list,dim = 'time')
mean_agg = xr.concat(mean_list,dim = 'time')

dims_mean = ['latitude','longitude','mean']
encodings_mean = { k:v for k,v in properties.NC_ENCODINGS.items() if k in dims_mean } 
dims_counts = ['latitude','longitude','counts']
encodings_counts = { k:v for k,v in properties.NC_ENCODINGS.items() if k in dims_counts } 

out_file = os.path.join(config['dir_out'],'-'.join([table,'no_reports_grid_ts',config['id_out'] + '.nc']))
nreports_agg.encoding =  encodings_counts
nreports_agg.to_netcdf(out_file,encoding = encodings_counts,mode='w')

out_file = os.path.join(config['dir_out'],'-'.join([table,'mean_grid_ts',config['id_out'] + '.nc']))
mean_agg.encoding =  encodings_mean
mean_agg.to_netcdf(out_file,encoding = encodings_mean,mode='w')
