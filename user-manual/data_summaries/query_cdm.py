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
import pandas as pd
from . import properties



# SOME COMMON PARAMS ----------------------------------------------------------
FILTER_PIVOT = 'report_id'


# SOME FUNCTIONS THAT HELP ----------------------------------------------------

def build_pd_query(table,**kwargs):
    filter_cols = []
    query_list = []
    if kwargs.get('filter_by_values'):
        if table in [ x[0] for x in kwargs['filter_by_values'].keys() ]:
            table_filter = { k:v for k,v in kwargs.get('filter_by_values').items() if table in k[0] }
            filter_cols.extend([ x[1] for x in table_filter.keys() ])
            for k,v in table_filter.items():
                values = [ '"' + x + '"' if type(x) == str else str(x) for x in v ]
                query_list.append(k[1] + ' in (' + ','.join(values) + ')')            
    if kwargs.get('filter_by_range'):        
        if table in [ x[0] for x in kwargs['filter_by_range'].keys() ]:
            table_filter = { k:v for k,v in kwargs.get('filter_by_range').items() if table in k[0] }
            filter_cols.extend([ x[1] for x in table_filter.keys() ])
            for k,v in table_filter.items():
                query_list.append( k[1] + ' >= ' + str(v[0]) + ' & ' + k[1] + ' <= ' + str(v[1]))
      
    return filter_cols,' & '.join(query_list)

def get_data_from_file(table, year, month, dir_data, **kwargs):
    # See if there is an external table to filter from 
    try:
        tables = []  
        if kwargs.get('filter_by_values'):
            tables.extend(list(set([ x[0] for x in kwargs['filter_by_values'].keys() ])))
        if kwargs.get('filter_by_range'):
            tables.extend(list(set([ x[0] for x in kwargs['filter_by_range'].keys() ])))
        filter_tables = list(set(tables))
        if table in filter_tables:
            tables.remove(table)
            
        if len(tables) > 0:
            for filter_table in tables:
                filter_cols, query = build_pd_query(filter_table,
                                    filter_by_values = kwargs.get('filter_by_values'),
                                    filter_by_range = kwargs.get('filter_by_range'))
                filter_cols.append(FILTER_PIVOT)
                filter_cols = list(set(filter_cols))        
                table_file = '-'.join(filter(None,[filter_table,str(year),str(month).zfill(2),kwargs.get('cdm_id')])) + '.psv'
                table_path = os.path.join(dir_data,table_file)
                iter_csv = pd.read_csv(table_path, usecols=filter_cols,iterator=True, chunksize=100000,delimiter='|')#properties.CDM_DELIMITER)
                df_filter = pd.concat([chunk.query(query)[FILTER_PIVOT] for chunk in iter_csv])
        else:
            df_filter = pd.Series()
            
        cols, query = build_pd_query(table,
                                    filter_by_values = kwargs.get('filter_by_values'),
                                    filter_by_range = kwargs.get('filter_by_range'))
        cols.extend(['latitude','longitude',FILTER_PIVOT])
        if kwargs.get('element'):
            cols.append(kwargs.get('element'))
        cols = list(set(cols))    
        table_file = '-'.join(filter(None,[table,str(year),str(month).zfill(2),kwargs.get('cdm_id')])) + '.psv'
        table_path = os.path.join(dir_data,table_file)  
        iter_csv = pd.read_csv(table_path, usecols=cols,iterator=True, chunksize=100000,delimiter='|')#properties.CDM_DELIMITER)
        df_list = []
        for chunk in iter_csv:
            if len(df_filter) > 0:
                chunk = chunk.loc[chunk[FILTER_PIVOT].isin(df_filter)]
            if len(query) > 0:
                chunk = chunk.query(query)
            df_list.append(chunk)
        df = pd.concat(df_list)
    except Exception as e:
        print(e)
        
    return df
    
    
def get_data_from_db():
    return

# FUNCTIONS TO DO WHAT WE WANT ------------------------------------------------
def query_monthly_table(table, year, month, dir_data = None,
                        db_con = None, cdm_id = None, element = None,
                        filter_by_values = None, 
                        filter_by_range = None):
    """Aggregate data from a monthly CDM table into a geographic grid.

    
    Arguments
    ---------
    table : str
        CDM table to aggregate
    year : int
        Year to aggregate
    month : int
        Month to aggregate
    
    Keyword arguments
    -----------------
    dir_data : str
        The path to the CDM table file(s)(filesystem query)
    db_con : object, optional
        db_con to tables (not avail yet, nor its other filters: source,deck...)
    cdm_id : str, optional
        String with the CDM table partition identifier (if any)
        (<table>-<year>-<month>-<cdm_id>.psv)
    element : str, optional
        CDM table element to aggregate. If None, only aggregation is counts.
    filter_by_values : dict, optional
        Dictionary with the {(table,element) :[values]} pairs to filter the data
        with. 
    filter_by_range : dict, optional
        Dictionary with the {(table,element) :[ini, end]} pairs to filter the 
        data with. 
    """
    
    # See this approach to read the data. With this for buoy data large file
    # the normal approach took more or less thes same. But probably
    # we'd benefit here with larger files or column selection...? With all
    # columns did not seem to be much different....
    if dir_data:
        kwargs = {'cdm_id' : cdm_id,'element' : element, 
                  'filter_by_values' : filter_by_values, 
                  'filter_by_range' : filter_by_range }
                     
        return get_data_from_file(table, year, month, dir_data, **kwargs)  
    elif db_con:
        return 'Not implemented'
    
    else:
        return 'Must provide a data directory or db connection'
    
    
            
    return
