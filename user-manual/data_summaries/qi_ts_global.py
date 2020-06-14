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
import glob
import pandas as pd
import logging

import datetime
from dateutil import rrule

from data_summaries import query_cdm
 

def value_counts(column):
    vc = cdm_table_ym[column].value_counts()
    vc.index = [ str(x) for x in vc.index ]
    buoys = cdm_table_ym[column].loc[cdm_table_ym['platform_type'] == 5 ]
    vc_buoys = buoys.value_counts() 
    vc_buoys.index = [ str(x) + '.buoys' for x in vc_buoys.index ]
    ships = cdm_table_ym[column].loc[cdm_table_ym['platform_type'] != 5 ]
    vc_ships = ships.value_counts()
    vc_ships.index = [ str(x) + '.ships' for x in vc_ships.index ]
    nreports = pd.Series(index=['nreports'],data=[len(cdm_table_ym)])
    nreports_ships = pd.Series(index=['nreports.ships'],data=[len(ships)])
    nreports_buoys = pd.Series(index=['nreports.buoys'],data=[len(buoys)])
    return pd.concat([nreports,nreports_buoys,nreports_ships,vc,vc_buoys,vc_ships])    
       
# MAIN ------------------------------------------------------------------------    
logging.basicConfig(format='%(levelname)s\t[%(asctime)s](%(filename)s)\t%(message)s',
                    level=logging.INFO,datefmt='%Y%m%d %H:%M:%S',filename=None)

#dir_data = sys.argv[1]
#dir_out = sys.argv[2]

dir_data = '/Users/iregou/C3S/data'
dir_out = dir_data
start_int = 1990
stop_int = 1990

# KWARGS FOR CDM FILE QUERY----------------------------------------------------
kwargs = {}
kwargs['dir_data'] = dir_data
kwargs['cdm_id'] = '*'
kwargs['columns'] = ['report_id','platform_type','report_quality','duplicate_status']
table = 'header'
# CREATE THE MONTHLY STATS ON THE DF PARTITIONS -------------------------------

duplicate_status = pd.DataFrame()
report_quality = pd.DataFrame()


start = datetime.datetime(start_int,1,1)
stop = datetime.datetime(stop_int,12,31)
for dt in rrule.rrule(rrule.MONTHLY, dtstart=start, until=stop):
    date_file = dt.strftime('%Y-%m')
    files_list = glob.glob(os.path.join(dir_data,'*','-'.join([table,date_file]) + '*.psv' ))
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
    
    loc_buoys = cdm_table_ym.loc[cdm_table_ym['platform_type'] == 5 ].index 
    loc_ships = cdm_table_ym.loc[cdm_table_ym['platform_type'] != 5 ].index
    
    ds = value_counts('duplicate_status')
    duplicate_status = pd.concat([duplicate_status,pd.DataFrame(data=[ds.values],index=[dt],columns = ds.index.values)])
    rq = value_counts('report_quality')    
    report_quality = pd.concat([report_quality,pd.DataFrame(data=[rq.values],index=[dt],columns = rq.index.values)])

out_file = os.path.join(dir_out,'report_quality_ts_global.psv')    
report_quality.to_csv(out_file,sep='|')

out_file = os.path.join(dir_out,'duplicate_status_ts_global.psv')    
duplicate_status.to_csv(out_file,sep='|')