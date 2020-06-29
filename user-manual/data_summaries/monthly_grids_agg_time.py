#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import xarray as xr
import datetime
import logging
import glob

from data_summaries import properties
 

# FUNCTIONS TO DO WHAT WE WANT ------------------------------------------------
def main(dir_data, nc_prefix = None, nc_suffix = None, start = None, stop = None,
         out_id = None, dir_out = None):
    """Aggregate monthly source deck summaries over time from nc files.

    
    Arguments
    ---------
    dir_data : str
        The path to the nc monthly files. 
    
    Keyword arguments
    -----------------
    nc_prefix : str, optional
        The nc filename field preceding the monthly id (prefix-yyyy-mm*)
    nc_suffix : str, optional
        The nc filename field after the monthly id (*yyyy-mm-suffix)
    start: datetime, optional
        First month to include
    stop: datetime, optional
        Last month to include
    out_id : str
        Basename for output filename
    dir_out : str, optional
        Output directory. 
    
    """    
    logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)

    
    pattern = '-'.join(filter(None,[nc_prefix,'????-??',nc_suffix])) + '.nc'  

        
    nc_files = glob.glob(os.path.join(dir_data,pattern))
    
    if len(nc_files) == 0:
        logging.warning('No nc files found for files {}'.format(pattern)) 
        return 1,1
            
    nc_files.sort()
    # Read all files to a single dataset
    dataset = xr.open_mfdataset(nc_files,concat_dim='time')
    # See how to provde for open periods (either start or stop)
    # Because there is no direct brace expansion in python, in glob, we do
    # the time slice selection, is any, here....
    if start and stop:
        dataset = dataset.sel(time=slice(start.strftime('%Y-%m-%d'), stop.strftime('%Y-%m-%d')))

    dataset = dataset.sortby('time')      
    # Aggregate each aggregation correspondingly....
    merged = {}
    aggregations = list(dataset.data_vars.keys())
    for aggregate in aggregations: # see if this works like this...might also appear lat/lon....
        if aggregate == 'max':
            merged[aggregate] = dataset[aggregate].max(dim='time',skipna=True)
        elif aggregate == 'min':
            merged[aggregate] = dataset[aggregate].min(dim='time',skipna=True)
        elif aggregate == 'mean':
            merged[aggregate] = dataset[aggregate].mean(dim='time',skipna=True)
        elif aggregate == 'counts':
            merged[aggregate] = dataset[aggregate].sum(dim='time',skipna=True)
        else:
            logging.warning('Aggregation {} not supported by script'.format(aggregate))
   
    # Merge aggregations to a single xarr
    xarr = xr.merge([ v.rename(k) for k,v in merged.items()])
    dims = ['latitude','longitude']
    dims.extend(aggregations)
    encodings = { x:properties.NC_ENCODINGS.get(x) for x in dims }
    xarr.encoding = encodings 
    # Save to nc
    if dir_out:  
        nc_name = out_id + '.nc' 
        xarr.to_netcdf(os.path.join(dir_out,nc_name),encoding = encodings)
    
    return 0,xarr

if __name__ == "__main__":
    
    # Dir data is now the direct path to the files to merge
    # It can be either a str (a release), or a dictionary 
    # (appending from different releases)
    config_file = sys.argv[1]
    
    with open(config_file) as cf:
        kwargs = json.load(cf)
    
    dir_data = kwargs['dir_data']
    
    # Start | stop now either integer or list, depending on dir_data
    if kwargs.get('start'):
        kwargs['start'] = datetime.datetime(kwargs['start'],1,1)
    if kwargs.get('stop'):
        kwargs['stop'] = datetime.datetime(kwargs['stop'],12,31)
        
    if not kwargs.get('dir_out'):
        kwargs['dir_out'] = dir_data
        
    no_tables = len(kwargs.get('tables'))
    non_avail_tables = 0
    for table in kwargs.get('tables'):
        logging.info('Merging table: {}'.format(table))
        kwargs_table = { x:kwargs.get(x) for x in ['start','stop','dir_out']}
        kwargs_table['nc_prefix'] =kwargs.get(table).get('nc_prefix')
        kwargs_table['nc_suffix'] =kwargs.get(table).get('nc_suffix')
        kwargs_table['out_id'] =kwargs.get(table).get('out_id')

        status,xarr = main(dir_data, **kwargs_table)
        non_avail_tables += status

    if non_avail_tables == no_tables:
        logging.error('No nc files found for tables: {}'.format(','.join(kwargs.get('tables'))))
        sys.exit(1)
    else:
        sys.exit(0)
    
