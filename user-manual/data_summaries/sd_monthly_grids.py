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

DEVS:
    This (functions using dask needs to work with env1 in C3S r092019)
    : because of some issues with pyarrow and
    the following with msgpack that had to be downgraded from 0.6.0 (default)
    to 0.5.6 after:
            
    File "msgpack/_unpacker.pyx", line 187, in msgpack._cmsgpack.unpackb
    ValueError: 1281167 exceeds max_array_len(131072)
    See https://github.com/tensorpack/tensorpack/issues/1003
"""

import os
import sys
import json
from dask import dataframe as dd
import dask.diagnostics as diag
import datashader as ds
import xarray as xr
import pandas as pd
import datetime
import logging
import glob
import time
import shutil

from data_summaries import properties
from data_summaries import query_cdm



# SOME FUNCTIONS THAT HELP ----------------------------------------------------
def bounds(x_range, y_range):
    return dict(x_range=x_range, y_range=y_range)

def create_canvas(bbox,degree_factor):
    plot_width = int(abs(bbox[0][0]-bbox[0][1])*degree_factor)
    plot_height = int(abs(bbox[1][0]-bbox[1][1])*degree_factor)    
    return ds.Canvas(plot_width=plot_width, plot_height=plot_height, **bounds(*bbox))
 
# FUNCTIONS TO DO WHAT WE WANT ------------------------------------------------
def main(sid_dck, year, month, dir_data = None, db_con = None, 
                     cdm_id = None, table = None, element = None,
                     aggregations = None, filter_by_values = None, 
                     filter_by_range = None, region = 'Global', 
                     resolution = 'lo_res', out_id = None, dir_out = None):
    """Aggregate data from a monthly CDM table into a geographic grid.

    
    Arguments
    ---------
    sid_dck : str
        Source and deck ID (sourceID-deckID)
    year : int
        Year to aggregate
    month : int
        Month to aggregate
    
    Keyword arguments
    -----------------
    dir_data : str, optional
        The path to the data level in the data release directory
    db_con : object, optional
        db_con to tables (not avail yet, nor its other filters: year, month...)
    cdm_id : str, optional
        String with the CDM table partition identifier (if any)
        (<table>-<year>-<month>-<cdm_id>.psv)
    table : str
        CDM table to aggregate
    element : str, optional
        CDM table element to aggregate. If None, only aggregation possible
        is counts.
    aggregations : list, optional
        List of aggregations to apply to the data element. 
        See properties.DS_AGGREGATIONS
    filter_by_values : dict, optional
        Dictionary with the {(table,element) :[values]} pairs to filter the data
        with. 
    filter_by_range : dict, optional
        Dictionary with the {(table,element) :[ini, end]} pairs to filter the 
        data with. 
    region : str
        Geographical region to subset the input data to. See properties.REGIONS
        for accepted values
    resolution : str
        Grid resolution to map the data to. 
        See properties.DEGREE_FACTOR_RESOLUTION
    out_id : str
        String with the output nc file identifier (<table>-<out_id>.nc)
    dir_out : str
        The parent path to the sid_dck subdirectory on output
    """
    
    
    # qc is the list of flags we want to keep, as integers, ideally, ok, include conversion just in case
    logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)
    
    # Get data in DF.
    # Prepare data query. Minimum elements for aggregation appended
    try:
        elements = [element] if element else ['report_id']
        datetime_element = 'report_timestamp' if table == 'header' else 'date_time'
        elements.extend(['latitude','longitude',datetime_element])
        # Make sure we don't repeat something requested by user
        elements = list(set(elements))
        
        kwargs = {'dir_data' : dir_data, 'db_con' : db_con,'cdm_id' : cdm_id,
                  'columns' : elements,'filter_by_values' : filter_by_values, 
                  'filter_by_range' : filter_by_range }
                      
        df = query_cdm.query_monthly_table(sid_dck, table, year, month, **kwargs)
    except:
        logging.error('Error querying data', exc_info=True)
        sys.exit(1)
    
    # Prepare aggregation
    canvas = create_canvas(properties.REGIONS.get(region),properties.DEGREE_FACTOR_RESOLUTION.get(resolution))
    if not element:
        aggregations = ['counts']
        element = 'latitude' # Count methid in ds.aggregations not working with no element
    
    date_time = datetime.datetime(int(year),int(month),1)
    
    # Aggregations directly to xr.dataset with method ds.summary()
    summary_kwargs = {}
    for agg in aggregations:
        summary_kwargs[agg] = properties.DS_AGGREGATIONS.get(agg)(element)

    xarr = canvas.points(df, 'longitude','latitude',
                         ds.summary(**summary_kwargs))    
    xarr = xarr.expand_dims(**{'time':[date_time]})

    dims = ['latitude','longitude']
    dims.extend(aggregations)
    encodings = { x:properties.NC_ENCODINGS.get(x) for x in dims }
    xarr.encoding = encodings 
    # Save to nc
    try: 
    	nc_name = '-'.join(filter(bool,[table,str(year),str(month).zfill(2),out_id])) + '.nc'
    	xarr.to_netcdf(os.path.join(dir_out,sid_dck,nc_name),encoding = encodings,mode='w')
    except:
        logging.info('Error saving nc:',exc_inc=True)
        logging.info('Retrying in 6 seconds...')
        time.sleep(6)
        xarr.to_netcdf(os.path.join(dir_out,sid_dck,nc_name),encoding = encodings,mode='w')
            
    return

if __name__ == "__main__":
    
    if len(sys.argv) == 2:
        config_file = sys.argv[1]
    else:
        dir_data = sys.argv[1]
        dir_out = sys.argv[2]
        sid_dck = sys.argv[3]
        year = sys.argv[4]
        month = sys.argv[5]
        config_file = sys.argv[6]
    
    with open(config_file) as cf:
        kwargs = json.load(cf)
  
    if len(sys.argv) > 2:
        kwargs['dir_data'] = dir_data
        kwargs['dir_out'] = dir_out
    else:
        sid_dck = kwargs['sid_dck'], kwargs['sid_dck'].pop('sid_dck')
        year = kwargs['year'], kwargs['year'].pop('year')
        month = kwargs['month'], kwargs['month'].pop('month')
     
    # Make table specs in json files (table.element) tuples
    for filter_type in ['filter_by_values','filter_by_range'] :
        if kwargs.get(filter_type):
            for kv in list(kwargs.get(filter_type).items()):
                kwargs[filter_type][(kv[0].split('.')[0],kv[0].split('.')[1])] = kwargs[filter_type].pop(kv[0])
    main(year, month, **kwargs)
