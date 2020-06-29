#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 09:24:24 2020

@author: iregon
"""
import os
import sys
sys.path.append('/Users/iregon/dessaas')
import glob
import json
import pandas as pd
import numpy as np
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LogNorm
import math

release_init = 1950
release_end = 2010

level2_config_path = '/Users/iregon/C3S/Release_092019/UserManual/L2_config.json' 
level2_path = os.path.dirname(level2_config_path)

level2_data_path = '/Users/iregon/C3S/Release_092019/reports/level2'

figsize=(14, 6)
font_size = 14
plt.rc('legend',**{'fontsize':font_size})        # controls default text sizes
plt.rc('axes', titlesize=font_size)     # fontsize of the axes title
plt.rc('axes', labelsize=font_size)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=font_size-2)    # fontsize of the tick labels
plt.rc('ytick', labelsize=font_size-2)    # fontsize of the tick labels
plt.rc('figure', titlesize=font_size)  # fontsize of the figure title

def get_nmonths_df():
    
    nmonths_partition = pd.DataFrame(index = item_list,columns=['nmonths'])

    for item in item_list:
        if partition == 'source':
            item_files = glob.glob(os.path.join(level2_data_path,item + '-*','no_reports-r092019-000000-all-ts.psv'))
        elif partition == 'deck':
            item_files = glob.glob(os.path.join(level2_data_path,'*-' + item,'no_reports-r092019-000000-all-ts.psv'))
            
        print('Source/deck, nfiles: {0}, {1} '.format(item,str(len(item_files))))
        
        item_df = pd.DataFrame(index = mon_index )
        for i,item_file in enumerate(item_files):
            item_dfi = pd.read_csv(item_file,delimiter='|',header=0,usecols=['yr-mo','header'],index_col='yr-mo',parse_dates=[0]).replace(0,np.nan)
            item_df = pd.concat([item_df ,item_dfi],axis=1,sort=False)
    
        nmonths_partition.loc[item] = len(item_df.sum(axis=1).replace(0,np.nan).dropna())
        
    nmonths_partition['hundreds'] = [i[0] for i in  nmonths_partition.index]
    nmonths_partition['units'] = [i[1:] for i in  nmonths_partition.index] 
    tuples_level2 =  [ (x[0],x[1]) for x in zip( nmonths_partition['hundreds'], nmonths_partition['units']) ]  
    nmonths_partition.index = tuples_level2 #pd.MultiIndex.from_tuples(tuples_level2,names=['hundreds','units'])
    nmonths_partition.drop(['hundreds','units'],axis=1,inplace=True)  
    
    return nmonths_partition

def nmonths_heatmap():
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize, dpi=150)
    hundreds = [ str(x) for x in range(0,10) ]
    units = [ str(x).zfill(2) for x in range(0,100) ]
    tuples = [ (h,u) for h in hundreds for u in units ]
    
    fig_path = os.path.join(level2_path,'number_of_months_per_{}'.format(partition))
    if partition == 'source':
        column_name = 'Source ID(ss)'
        index_name = 'Source ID(S)'
        column_add = ''
        index_add = ''
        partition_ID = 'Sss'
    elif partition == 'deck':
        column_name = 'Deck ID(dd)'
        index_name = 'Deck ID(D)'
        column_add = ''
        index_add = ''
        partition_ID = 'Ddd'
    heatmap = pd.DataFrame(index = tuples,columns=['nmonths'])
    
    heatmap['nmonths'] = nmonths_df['nmonths']
    tuples_axis = [ (h + column_add ,index_add + u) for h in hundreds for u in units ]
    multiindex = pd.MultiIndex.from_tuples(tuples_axis,names=[index_name,column_name])
    heatmap.index= multiindex
    heatmap2 = heatmap.reset_index().pivot(columns=column_name,index=index_name,values='nmonths')
    heatmap2 = heatmap2.iloc[::-1]
    heatmap2 = heatmap2.replace(0,np.nan)
    
    log_norm = LogNorm(vmin=heatmap2.min().min(), vmax=heatmap2.max().max())
    cbar_ticks = [math.pow(10, i) for i in range(math.floor(math.log10(heatmap2.min().min())), 1+math.ceil(math.log10(heatmap2.max().max())))]
    cbar_kws = {'label':'No. months','ticks': cbar_ticks}

    sns.heatmap(heatmap2,ax = ax,  cbar_kws = cbar_kws,linewidths = 0.1, linecolor='LightGrey', norm = log_norm)
    plt.yticks(rotation=0)
    plt.title('Number of months with data per {0} ({1}) \n Release r092019 ({2} to {3})'.format(partition,partition_ID,str(release_init),str(release_end)))
    plt.savefig(fig_path,bbox_inches='tight',dpi = 300)
    plt.close(fig)

    return


    
# Open list with final selection of source-decks in release and do some cleaning
with open(level2_config_path,'r') as fileObj:
    level2_config = json.load(fileObj)
    
level2_config.pop('params_exclude',None)


# Drop excluded SID-DECK             
for sd in list(level2_config.keys()):
    if level2_config.get(sd).get('exclude'):
        print('SID-DCK excluded: {}'.format(sd))
        level2_config.pop(sd,None)

# Get the sources and decks with the imma1 code_tables description
level2_sources_list =  list(sorted(set([ x[0:3] for x in level2_config.keys() ]))) 
level2_decks_list =  list(sorted(set([ x[4:] for x in level2_config.keys() ]))) 


# Get number of months with data from sources
mon_index = pd.date_range(start=datetime.datetime(release_init,1,1),end=datetime.datetime(release_end,12,1),freq='MS')

item_list = level2_sources_list
partition = 'source'
nmonths_df = get_nmonths_df()
nmonths_heatmap()

item_list = level2_decks_list
partition = 'deck'
nmonths_df = get_nmonths_df()
nmonths_heatmap()


