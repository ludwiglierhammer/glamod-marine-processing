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
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LogNorm
import math
import matplotlib as mpl


drifters = ['063-714']

release_init = 1950
release_end = 2010



level2_config_path = '/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/r092019_000000/ICOADS_R3.0.0T/L2_config.json' 
level2_data_path = '/group_workspaces/jasmin2/glamod_marine/data/r092019/ICOADS_R3.0.0T/level2'


figsize=(12, 6)

param_ordered = ['AT','SST','DPT','WBT','SLP','WD','WS']

def join_reports_platforms():   
    nreports_passed_all = pd.DataFrame(index = mon_index)
    nreports_passed_all = pd.concat([nreports_passed_all,nreports_passed_s],axis=1,sort=False)
    nreports_passed_all = pd.concat([nreports_passed_all,nreports_passed_d],axis=1,sort=False)
   
    columns = list(nreports_passed_all.columns)
    columns = list(set(columns))
    nreports_passed_all['reports_total'] = nreports_passed_all['reports'].sum(axis=1)
    nreports_passed_all.drop(['reports'],axis=1,inplace = True)
    columns.remove('reports')
    
    for col in columns:
        nreports_passed_all['total_' + col] = nreports_passed_all[[col]].sum(axis=1) 

    drop = [ x for x in nreports_passed_all.columns if x.split('_')[0] not in ['total','reports'] ]
    nreports_passed_all.drop(drop,axis=1,inplace=True)  
    replace = { x:x.split('_')[1] for x in nreports_passed_all.columns }
    replace.update({'reports_total':'reports'})
    nreports_passed_all.rename(columns=replace,inplace = True)     
    return nreports_passed_all

def join_quality_platforms():   
    nquality_all = pd.DataFrame(index = mon_index)
    nquality_all = pd.concat([nquality_all,nquality_s],axis=1,sort=False)
    nquality_all = pd.concat([nquality_all,nquality_d],axis=1,sort=False)
   
    columns = list(nquality_all.columns)
    columns = list(set(columns))
    nquality_all['total_reports'] = nquality_all['total'].sum(axis=1)
    nquality_all.drop(['total'],axis=1,inplace=True) 
    
    for col in columns:
        if col == 'total':
            continue
        nquality_all['total_' + col] = nquality_all[[col]].sum(axis=1) 

    drop = [ x for x in nquality_all.columns if x.split('_')[0] != 'total' ]
    nquality_all.drop(drop,axis=1,inplace=True)  
    nquality_all.rename(columns={"total_reports": "total", "total_0": "0","total_1": "1","total_2": "2"},inplace = True)     
    return nquality_all

def join_dups_platforms():   
    dups_all = pd.DataFrame(index = mon_index)
    dups_all = pd.concat([dups_all,dups_s],axis=1,sort=False)
    dups_all = pd.concat([dups_all,dups_d],axis=1,sort=False)
   
    columns = list(dups_all.columns)
    columns = list(set(columns))
    dups_all['total_reports'] = dups_all['total'].sum(axis=1)
    dups_all.drop(['total'],axis=1,inplace=True) 
    
    for col in columns:
        if col == 'total':
            continue
        dups_all['total_' + col] = dups_all[[col]].sum(axis=1) 

    drop = [ x for x in dups_all.columns if x.split('_')[0] != 'total' ]
    dups_all.drop(drop,axis=1,inplace=True)  
    dups_all.rename(columns={"total_reports": "total", "total_unique-best": "unique-best","total_unchecked": "unchecked","total_duplicates": "duplicates"},inplace = True)     
    return dups_all



def plot_all_ts(): 
    fig_path = os.path.join(level2_data_path,'reports','global_numbers_ts.jpg')
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize, dpi=150)
    
    
    colors = ['CornflowerBlue','LightSkyBlue','PowderBlue','OliveDrab','YellowGreen','YellowGreen' ]
    ax.stackplot(mon_index,nquality_s['0'],nquality_s['1'],nquality_s['2'],nquality_d['0'],nquality_d['1'],nquality_d['2'],colors =colors)
    ax.plot(mon_index,nquality_s['total'],color ='DarkSlateGray',linewidth = 1)
    ax.plot(mon_index,nquality_d['total'] + nquality_s['total'],color ='DarkSlateGray',linewidth = 1)
    ax.set_xlim([mon_index[0], mon_index[-1]])
    
    ax.set_ylabel('No. reports', color='k')
    ax.grid(linestyle=':',which='major')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.1E}'))
    ax.title.set_text('Total number of reports in Release 1')
    plt.savefig(fig_path,bbox_inches='tight',dpi = 300)
    plt.close(fig)
    

    return

def get_nreports_df():   
    nreports_passed = pd.DataFrame(index = mon_index)
    nquality = pd.DataFrame(index = mon_index)
    ndups = pd.DataFrame(index = mon_index)
    item_list_platform = item_list.copy() if platform == 'ships' else drifters
    if platform == 'ships':
        for i in drifters:
            item_list_platform.remove(i)
        
    for item in item_list_platform:
        item_files = glob.glob(os.path.join(level2_data_path,'reports',item,'no_reports-r092019-000000-qcr0-qc0-ts.psv'))
        quality_files = glob.glob(os.path.join(level2_data_path,'reports',item,'report_quality-r092019-000000-ts.psv'))
        dup_files = glob.glob(os.path.join(level2_data_path,'reports',item,'duplicate_status-r092019-000000-ts.psv'))
        for i,(item_file,quality_file,dup_file) in enumerate(zip(item_files,quality_files,dup_files)):
            try:
                item_dfi = pd.read_csv(item_file,delimiter='|',header=0,index_col='yr-mo',parse_dates=[0]).replace(0,np.nan)
                nreports_passed = pd.concat([nreports_passed ,item_dfi],axis=1,sort=False)
            except Exception as e:
                print('No data found in {0}'.format(item))
                print(e)
                pass
            try:
                quality_dfi = pd.read_csv(quality_file,delimiter='|',header=0,index_col='yr-mo',parse_dates=[0]).replace(0,np.nan)
                nquality = pd.concat([nquality ,quality_dfi],axis=1,sort=False)
            except Exception as e:
                print('No data found in {0}'.format(item))
                print(e)
                pass             
            
            try:
                dup_dfi = pd.read_csv(dup_file,delimiter='|',header=0,index_col='yr-mo',parse_dates=[0]).replace(0,np.nan) 
                ndups = pd.concat([ndups ,dup_dfi],axis=1,sort=False)
            except Exception as e:
                print('No data found in {0}'.format(item))
                print(e)
                pass
    
    obs_tables = list(set([ x for x in nreports_passed.columns if 'observations' in x ]))
    try:
        nreports_passed['reports'] = nreports_passed[['header']].sum(axis=1)
        nreports_passed.drop(['header'],axis=1,inplace =True)
        for table in obs_tables:
            param = table.split('-')[1].upper()
            nreports_passed[param] = nreports_passed[[table]].sum(axis=1)   
        nreports_passed.drop(obs_tables,axis=1,inplace =True)
    except Exception as e:
        columns = ['reports']
        columns.extend(obs_tables)
        nreports_passed[columns] = 0
        nreports_passed = nreports_passed[columns]
        print('No passed reports in platform {}'.format(platform))
        print(e)
        
    qc_flags = list(set([ x for x in nquality.columns if x != 'total' ]))
    try:        
        nquality['total_reports'] = nquality[['total']].sum(axis=1)
        nquality.drop( ['total'] ,axis=1,inplace =True)
        for qc in qc_flags:
            nquality['total_' + qc] = nquality[[qc]].sum(axis=1) 
        nquality.drop( qc_flags ,axis=1,inplace =True)
        nquality.rename(columns={"total_reports": "total", "total_0": "0","total_1": "1","total_2": "2"},inplace = True)
    except Exception as e:
        columns = ['total']
        columns.extend(qc_flags)
        nquality[columns] = 0
        nquality = nquality[columns]
        print('No quality monitoring in platform {}'.format(platform))
        print(e)  
     
    dup_flags = list(set([ x for x in ndups.columns if x != 'total' ]))
    if '0' in dup_flags:
        ndups.rename(columns={'0': '1'},inplace = True)  

    if '0' in dup_flags or '1' in dup_flags:
        ndups['unique-best'] = ndups[['1']].sum(axis=1)
        ndups.drop(['1'],axis=1,inplace =True)
    else:
        ndups['unique-best'] = 0
        
    if '2' in dup_flags:
        ndups.rename(columns={'2': '3'},inplace = True)  

    if '2' in dup_flags or '3' in dup_flags:
        ndups['duplicates'] = ndups[['3']].sum(axis=1)
        ndups.drop(['3'],axis=1,inplace =True)
    else:
        ndups['duplicates'] = 0

    if '4' in dup_flags:
        ndups['unchecked'] = ndups[['4']].sum(axis=1)
        ndups.drop(['4'],axis=1,inplace =True)
    else:
        ndups['unchecked'] = 0

    ndups.drop(['total'],axis=1,inplace =True)
    ndups['total'] = ndups[['unique-best','unchecked','duplicates']].sum(axis=1)
    
    return nreports_passed,nquality,ndups[['unique-best','unchecked','duplicates','total']]

def get_write_summaries():
    no_reports_total = nquality_df['total'].sum()

    fileObj.write('\n\tREPORT DUPLICATE STATUS (percents with respect to the total number of ship reports):\n')
    for dup in ['unique-best','unchecked','duplicates']:
        try:
            fileObj.write('\t\t{0}: {1:.0f}, {2:.1f}%\n'.format(dup, dup_reports_df[dup].sum(),100*dup_reports_df[dup].sum()/no_reports_total))
        except:
            fileObj.write('\t\tNo dup={} observations\n'.format(dup))
            pass

    fileObj.write('\n\tREPORT QUALITIES (percents with respect to the total number of ship reports):\n')
    for qc in ['0','1','2']:
        try:
            fileObj.write('\t\t{0}: {1:.0f}, {2:.1f}%\n'.format(qc, nquality_df[qc].sum(),100*nquality_df[qc].sum()/no_reports_total))
        except:
            fileObj.write('\t\tNo qc={} observations\n'.format(qc))
            pass 
 

    
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
level2_list =  [ x for x in level2_config.keys() ]

# Get number of months with data from sources
mon_index = pd.date_range(start=datetime.datetime(release_init,1,1),end=datetime.datetime(release_end,12,1),freq='MS')

item_list = level2_list

platform = 'ships'
nreports_passed_s,nquality_s,dups_s = get_nreports_df()
platform = 'drifters'
nreports_passed_d,nquality_d,dups_d = get_nreports_df()


nreports_passed_all = join_reports_platforms()
nquality_all = join_quality_platforms()
dups_all = join_dups_platforms()

with open(os.path.join(level2_data_path,'reports','L2_global_numbers.txt'),'w') as fileObj:
    totals = dict()
    totals['reports'] = nquality_all['total'].sum()
    fileObj.write('TOTAL NUMBER OF REPORTS (ALL QUALITIES): {0:.0f}\n\n'.format(totals['reports']))
    fileObj.write('\tSHIPS REPORTS (ALL QUALITIES): {0:.0f}, {1:.1f}%\n\n'.format(nquality_s['total'].sum(),100*nquality_s['total'].sum()/totals['reports']))
    fileObj.write('\tDRIFTERS REPORTS (ALL QUALITIES): {0:.0f}, {1:.1f}%\n\n'.format(nquality_d['total'].sum(),100*nquality_d['total'].sum()/totals['reports']))
    fileObj.write('REPORT QUALITIES (percents with respect to the total number of reports):\n')
    for qc in ['0','1','2']:
        totals[qc] = nquality_all[qc].sum()
        qc_p = 100*totals[qc]/totals['reports']      
        fileObj.write('\t{0}: {1:.0f}, {2:.1f}%\n'.format(qc, totals[qc],qc_p))
    
    fileObj.write('\nREPORT DUPLICATE STATUS (percents with respect to the total number of reports):\n')
    for dup in ['unique-best','unchecked','duplicates']:
        totals[dup] = dups_all[dup].sum()
        dup_p = 100*totals[dup]/totals['reports']      
        fileObj.write('\t{0}: {1:.0f}, {2:.1f}%\n'.format(dup, totals[dup],dup_p))
        
    params = list(set([ x for x in nreports_passed_all.columns if x != 'total' ]))
    fileObj.write('\nNUMBER OF OBSERVED PARAMETERS, PASSED QC REPORT AND PARAMETER ONLY\n')
    fileObj.write('(percents with respect to the total number of  passed reports):\n')
    for param in params:
        totals[param] = nreports_passed_all[param].sum()
        param_p = 100*totals[param]/totals['0'] 
        try:
            param_s = nreports_passed_s[param].sum()
        except:
            param_s = 0
            pass
        try:
            param_d = nreports_passed_d[param].sum() 
        except:
            param_d = 0
            pass
        fileObj.write('\t{0}: {1:.0f}, {2:.1f}% of total passed reports\n'.format(param, totals[param],param_p))
        fileObj.write('\t\tShip {0}: {1:.0f}\n'.format(param, param_s))
        fileObj.write('\t\tDrifters {0}: {1:.0f}\n'.format(param, param_d))
        
    
    fileObj.write('\n\nSUMMARY FOR SHIPS\n') 
    platform = 'ships'
    nquality_df = nquality_s
    no_reports_df = nreports_passed_s
    dup_reports_df = dups_s
    get_write_summaries()
    fileObj.write('\n\nSUMMARY FOR DRIFTERS\n')
    platform = 'drifters'
    nquality_df = nquality_d
    no_reports_df = nreports_passed_d
    dup_reports_df = dups_d
    get_write_summaries()


plot_all_ts()    




