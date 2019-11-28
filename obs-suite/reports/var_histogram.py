#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 21 16:06:16 2019

We want a set of data descriptors on a monthly lat-lon box grid:
    - counts, max, min, mean
    
We want to have the stats for the qced and not qced thing
    
We want to save that to a nc file to open afterwards in notebooks 
and inspect further or to create static images (maps, plots, etc....) for reports

We are not doing it on the notebooks because we are running these interactively
 and these depend on the changing memo availability of the sci servers.
An alternative will be to run the notebook as a bsub job, but we would need
to know before hand, our memo requirements.

When we have experience with this, we can add the option to (re)compute the nc
 file in the notebook.


We use datashader to create the spatial aggregates because dask does not support
dataframe.cut, which is essential to do a flexible groupby coordinates. We could
groupby(int(coordinates)), but the we would be limited to 1degree boxes, which 
is not bad, but we don't wnat to be limited.  

@author: iregon
"""

import os
from dask import dataframe as dd
import dask.diagnostics as diag
import matplotlib.pyplot as plt
import datashader as ds
import xarray as xr
import pandas as pd
from cdm import properties
import logging
import glob
import sys
import json
import shutil
import numpy as np

script_path = os.path.dirname(os.path.realpath(__file__))
# SOME PARAMETERS -------------------------------------------------------------
FFS = '-'
CDM_DTYPES = {'latitude':'float32','longitude':'float32',
              'observation_value':'float32','date_time':'object',
              'quality_flag':'int8','crs':'int','report_quality':'int8',
              'report_id':'object'}
READ_COLS = ['report_id','latitude','longitude','observation_value','date_time',
                 'quality_flag']
DTYPES = { x:CDM_DTYPES.get(x) for x in READ_COLS }
DELIMITER = '|'

param_check_limit = {'ws':50}
param_range = {'ws':[0,100]}
param_bins = {}
for param,ranges in param_range.items():
    param_bins[param] = ranges[1] - ranges[0] 
    
FIGSIZE = (12, 6)
FIGSIZE_TS = (12, 3)
MARKERSIZE = 2
with open(os.path.join(script_path,'var_properties.json'),'r') as f:
    var_properties = json.load(f)
    
#------------------------------------------------------------------------------

def main():   
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    try:
        data_path = sys.argv[1]
        release = sys.argv[2]
        update = sys.argv[3]
        source = sys.argv[4]
        sid_dck = sys.argv[5] 
        param = sys.argv[6]
        scratch_dir = sys.argv[7]
    except Exception as e:
        logging.error(e, exc_info=True)
        sys.exit(1)

#    data_path = '/Users/iregon/dessaps/data'
#    release = 'r092019'
#    update = '000000'
#    source = 'ICOADS_R3.0.0T'
#    sid_dck = '002-150' 
#    param = 'ws'
#    scratch_dir = '/Users/iregon/dessaps/data/002-150'

    level='level1e'
    cdm_id = FFS.join([release,update])
    
    var_file_pattern = os.path.join(data_path,release,source,level,sid_dck,FFS.join(['observations',param,'*',cdm_id]) + '.psv')   
#    var_file_pattern = os.path.join(data_path,sid_dck,FFS.join(['observations',param,'*',release,update]) + '.psv')
    var_files = glob.glob(var_file_pattern)
    
    if len(var_files) == 0:
        logging.warning('Parameter {0}. No files found {1}'.format(param,var_file_pattern)) 
            
    obs_df = dd.read_csv(var_file_pattern,delimiter = DELIMITER,usecols = READ_COLS,parse_dates=['date_time'],dtype = DTYPES)
    logging.info('Saving obs file to parquet in {}'.format(scratch_dir))
    
    obs_parq_path = os.path.join(scratch_dir,param + '.parq.tmp')
    with diag.ProgressBar(), diag.Profiler() as prof, diag.ResourceProfiler(0.5) as rprof:
        obs_df.to_parquet(obs_parq_path)
    del obs_df
    
    try:
        logging.info('Reading data from parquet')
        with diag.ProgressBar(), diag.Profiler() as prof, diag.ResourceProfiler(0.5) as rprof:
            obs_df = dd.read_parquet(obs_parq_path)
        
        nobs = len(obs_df.compute())
        
        param_offset = var_properties['offset'].get(param)
        param_scale = var_properties['scale'].get(param)
        units = var_properties['units'].get(param)
        obs_df['observation_value'] = param_offset + param_scale*obs_df['observation_value']    
           
        param_over_limit = obs_df['observation_value'].loc[obs_df['observation_value']>param_check_limit.get(param)].count().compute()
        percent_over_limit = 100*param_over_limit/nobs
        logs = [True,False]
        for log in logs:
            fig, ax = plt.subplots(nrows=1, ncols=1, figsize=FIGSIZE, dpi=150) 
            ax2 = ax.twinx()
            n,bins,patches = ax.hist(obs_df['observation_value'].compute(), density = True,log=log, bins=param_bins.get(param), range=param_range.get(param)) 
            n,bins,patches = ax2.hist(obs_df['observation_value'].compute(), color='red',alpha=0.1,log=log, bins=param_bins.get(param), range=param_range.get(param))
            
            # last non-zero bin, and get one extra for security and clarity
            ls = [i for i, e in enumerate(n) if e != 0]
            last = ls[-1]
            last = last + 1 if last<len(bins) else last
            x0 = param_range.get(param)[0]
            x1 = param_range.get(param)[1]#bins[last]
            
            ax.set_xlim(x0,x1)
            ax2.set_xlim(x0,x1)
            ax.set_ylabel('density', color='k')
            ax2.set_ylabel('counts', color='k')
            ax.set_xlabel(param + ' (' + units + ')', color='k')
            
            title = ' '.join([sid_dck,param,'histogram'])+ "\n" + "{0:.2f}% over {1:.1f} {2}".format(percent_over_limit,param_check_limit.get(param),units)
            ax.grid(linestyle=':',which='both',color='grey') 
            plt.title(title)  
            plt.tight_layout();
            plt.xticks(np.arange(x0, x1, 10))
            # And save plot and data
            if log:
                out_file = os.path.join(data_path,release,source,level,'reports',sid_dck,FFS.join([sid_dck,'observations',param,'histogram','log']) + '.png')
            else:
                out_file = os.path.join(data_path,release,source,level,'reports',sid_dck,FFS.join([sid_dck,'observations',param,'histogram']) + '.png')
            plt.savefig(out_file,bbox_inches='tight',dpi = 300)

        
        shutil.rmtree(obs_parq_path)
        
        ts_nc_path = os.path.join(data_path,release,source,level,'reports',sid_dck,FFS.join(['observations',param,release,update,'all','ts.nc']))
#        ts_nc_path = os.path.join(data_path,FFS.join(['observations',param,release,update,'all','ts.nc']))
        out_file = os.path.join(data_path,release,source,level,'reports',sid_dck,FFS.join([sid_dck,'observations',param,'all','ts','global']) + '.png')
        ts_lat = xr.open_dataset(ts_nc_path)
        ts_lat['counts all'] = ts_lat['counts all reports'].sum(dim='latitude_bins',skipna=True)
        ts_lat['mean all'] = ts_lat['mean'].mean(dim='latitude_bins',skipna=True)
        ts_lat['max all'] = ts_lat['max'].max(dim='latitude_bins',skipna=True)
        ts_lat['min all'] = ts_lat['min'].min(dim='latitude_bins',skipna=True)
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=FIGSIZE_TS, dpi=150) 
        ax.plot(ts_lat['time'],ts_lat['max all'],marker = '.',linestyle=' ',color='OrangeRed',label='_nolegend_',markersize = MARKERSIZE,zorder=7)
        ax.plot(ts_lat['time'],ts_lat['min all'],marker = '.',linestyle=' ',color='OrangeRed',label='min/max',markersize = MARKERSIZE,zorder=7)
        ax.plot(ts_lat['time'],ts_lat['mean all'],linestyle ='-',color='black',label='mean',zorder=6)
        ax.set_ylabel(units, color='k')
        ax.grid(linestyle=':',which='major')
        ax.set_ylim(x0,x1)
        ax2 = ax.twinx()
        ax2.fill_between(ts_lat['time'].values,0,ts_lat['counts all'].astype('float'), facecolor='Grey',alpha=0.25,interpolate=False,label='no.reports',zorder=1)
        ax2.set_ylabel('counts', color='k')
        ax.set_zorder(ax2.get_zorder()+1) # put ax in front of ax2
        ax.patch.set_visible(False) 
        lines2, labels2 = ax2.get_legend_handles_labels() 
        lines, labels = ax.get_legend_handles_labels()
        ncols_leg = 4      
        ax.legend(lines + lines2,labels + labels2,loc='center', bbox_to_anchor=(0.5, -0.15),ncol=ncols_leg)
        plt.savefig(out_file,bbox_inches='tight',dpi = 300)
        plt.close(fig)
    except Exception:
        logging.info('Error processing',exc_info=True)
        shutil.rmtree(obs_parq_path)
        
if __name__ == '__main__':
    main()        
