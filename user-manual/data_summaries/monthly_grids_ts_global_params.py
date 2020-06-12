#!/usr/bin/env python3
#
#  Needs to run with py env2: bwcause of pandas to_parquet (different to dask to parquet!)
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 09:24:24 2020

@author: iregon
"""
import os
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

# FUNCTIONS -------------------------------------------------------------------
def bounds(x_range, y_range):
    return dict(x_range=x_range, y_range=y_range)

def create_canvas(bbox,degree_factor):
    plot_width = int(abs(bbox[0][0]-bbox[0][1])*degree_factor)
    plot_height = int(abs(bbox[1][0]-bbox[1][1])*degree_factor)    
    return ds.Canvas(plot_width=plot_width, plot_height=plot_height, **bounds(*bbox))
    
def aggs_counts(qc = False):
#    if qc:
#        month_par = df.get_partition(i)
#        month_data = month_par.loc[month_par['quality_flag']==0].compute()
#    else:
#        month_data = df.get_partition(i).compute()
    #if qc == True:
    #    return canvas.points(cdm_table.loc[(cdm_table['report_quality']==0) & (cdm_table['quality_flag'] == 0)],'longitude','latitude',ds.count('report_quality'))     
    #else:
    return canvas.points(cdm_table,'longitude','latitude',ds.count('observation_value'))      

def aggs_value(qc = False):
#    if qc:
#        month_par = df.get_partition(i)
#        month_data = month_par.loc[month_par['quality_flag']==0].compute()
#    else:
#        month_data = df.get_partition(i).compute()
    #if qc == True:
    #    return canvas.points(cdm_table.loc[(cdm_table['report_quality']==0) & (cdm_table['quality_flag'] == 0)],'longitude','latitude',ds.mean('observation_value'))     
    #else:
    return canvas.points(cdm_table,'longitude','latitude',ds.mean('observation_value'))

# END FUNCTIONS ---------------------------------------------------------------
        
# MAIN ------------------------------------------------------------------------    

dir_data = '/group_workspaces/jasmin2/glamod_marine/data/user_manual/v4/level2'
dir_out  = '/group_workspaces/jasmin2/glamod_marine/data/user_manual/v4/level2/quicklooks/'  
table = 'observations-sst'
start = datetime.datetime(2010,1,1)
stop = datetime.datetime(2010,12,31)
region = 'Global'
resolution = 'lo_res'

logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)


# KWARGS FOR CDM FILE QUERY
kwargs = {}
kwargs['dir_data'] = dir_data
kwargs['cdm_id'] = '*'
kwargs['columns'] = ['latitude','longitude','date_time','observation_value']
kwargs['filter_by_values'] = {('header','report_quality'):[0],('observations-sst','quality_flag'):[0]}

canvas = create_canvas(properties.REGIONS.get(region),properties.DEGREE_FACTOR_RESOLUTION.get(resolution))

# CREATE THE MONTHLY STATS ON THE DF PARTITIONS
nreports_list = []
mean_list = []

for dt in rrule.rrule(rrule.MONTHLY, dtstart=start, until=stop):
    date_file = dt.strftime('%Y-%m')
    logging.info('PROCESSING TIME PARTITION: {}'.format(date_file))
    parq_path = os.path.join(dir_out,'-'.join([date_file,table,'.data.parq.tmp']))
    logging.info('PARQUET PATH: {}'.format(parq_path))
    logging.info('SEARCH PATH: {}'.format(os.path.join(dir_data,'*','-'.join([table,date_file]) + '*.psv' )))
    files_list = glob.glob(os.path.join(dir_data,'*','-'.join([table,date_file]) + '*.psv' ))
    if len(files_list) == 0:
        logging.warning('No data files for time partition {}'.format(date_file))
        continue

    print(files_list)
    sid_dck_list = [ os.path.basename(os.path.dirname(x)) for x in files_list ]
    print(sid_dck_list)
    cdm_table_ym = pd.DataFrame()
    for sid_dck in sid_dck_list:
        logging.info('Aggregating sd {}'.format(sid_dck))
        cdm_table = query_cdm.query_monthly_table(sid_dck, table, dt.year, dt.month, **kwargs)
        cdm_table.dropna(inplace = True)
        cdm_table_ym = pd.concat([cdm_table_ym,cdm_table], sort = False)
    # SAVE TO PARQUET AND READ DF BACK FROM THAT TO ENHANCE PERFORMANCE
    # CHECK HERE NUMBER OF RECORDS AFTER AND BEFORE SAVING, ETC....
    print('to parquet')
    with diag.ProgressBar(), diag.Profiler() as prof, diag.ResourceProfiler(0.5) as rprof:
        #append = False if i == 0 else True
        #cdm_table.to_parquet(parq_path, engine = 'pyarrow',mode='a')#, compression = 'gzip', append = append)
        #cdm_table_ym.to_parquet(parq_path, engine = 'fastparquet', compression = 'gzip', append = append)
        cdm_table_ym.to_parquet(parq_path, engine = 'fastparquet', compression = 'gzip',append = False)  
    del cdm_table_ym
        
    print('From parquet')
    cdm_table = dd.read_parquet(parq_path)
    
    nreports_arr = aggs_counts().assign_coords(time=dt).rename('counts')
    mean_arr = aggs_value().assign_coords(time=dt).rename('mean')
    nreports_list.append(nreports_arr)
    mean_list.append(mean_arr)

#    Now this seems different with pandas to parquet, is it the engine choice?
#    shutil.rm(parq_path)
    os.remove(parq_path)

    
nreports_agg = xr.concat(nreports_list,dim = 'time')
mean_agg = xr.concat(mean_list,dim = 'time')

dims_mean = ['latitude','longitude','mean']
encodings_mean = { k:v for k,v in properties.NC_ENCODINGS.items() if k in dims_mean } 
dims_counts = ['latitude','longitude','counts']
encodings_counts = { k:v for k,v in properties.NC_ENCODINGS.items() if k in dims_counts } 

out_file = os.path.join(dir_out,'-'.join([table,'total_no_reports_grid_ts.nc']))
nreports_agg.encoding =  encodings_counts
nreports_agg.to_netcdf(out_file,encoding = encodings_counts,mode='w')

out_file = os.path.join(dir_out,'-'.join([table,'total_mean_grid_ts.nc']))
mean_agg.encoding =  encodings_mean
mean_agg.to_netcdf(out_file,encoding = encodings_mean,mode='w')
