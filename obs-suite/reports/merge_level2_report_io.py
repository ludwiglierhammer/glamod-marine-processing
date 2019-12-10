#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 20 11:43:22 2018




@author: iregon
"""
import os
import sys
import json
import logging
import datetime
import pandas as pd
import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import numpy as np
import matplotlib.dates as mdates

#if sys.version_info[0] >= 3:
#    py3 = True
#else:
#    py3 = False
#
#this_script = main.__file__
#
## PROCESS INPUT PARAMETERS AND INITIALIZE SOME STUFF ==========================
## 1. From command line
#indir='/Users/iregon/C3S/C3S_beta_release_sid-deck_reports/numbers_numbers'
#ingest_dir=os.path.join(indir,'ingest')
#reject_dir=os.path.join(indir,'reject')
#
#buoys='063-714'
# 2. Some plotting options
font_size_legend = 11
axis_label_size = 11
tick_label_size = 9
title_label_size = 14
figsize=(14, 6)


## Colors for vari numbers
vars_color = dict()
vars_color['sst'] = 'Yellow'
vars_color['at'] = 'Gold'
vars_color['slp'] = 'YellowGreen'
vars_color['wd'] = 'DeepSkyBlue'
vars_color['ws'] = 'LightSteelBlue'
vars_color['dpt'] = 'Pink'
vars_color['wbt'] = 'LavenderBlush'
## END PARAMS ==================================================================
## FUNCTIONS  ==================================================================
#def read_data():
#    # Get file paths and read files to df. Merge in single df by report_id
#    df_varis = pd.read_csv(fil,sep=",",parse_dates=[0],header=[0])
#    df_varis.set_index(['date'],inplace=True)
#    return df_varis
#
#def plot_df():
#    plt.rc('legend',**{'fontsize':font_size_legend})          # controls default text sizes
#    plt.rc('axes', titlesize=axis_label_size)     # fontsize of the axes title
#    plt.rc('axes', labelsize=axis_label_size)    # fontsize of the x and y labels
#    plt.rc('xtick', labelsize=tick_label_size)    # fontsize of the tick labels
#    plt.rc('ytick', labelsize=tick_label_size)    # fontsize of the tick labels
#    plt.rc('figure', titlesize=title_label_size)  # fontsize of the figure title
#    
#    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize, dpi=150) 
#    ax.fill_between(df.loc[df['imma']>0].index,0,df['imma'].loc[df['imma']>0].astype('float'), facecolor='DarkGrey',alpha=0.45,interpolate=False,label='IMMA1 selection',zorder=1)
#    ax.fill_between(df.loc[df['header']>0].index,0,df['header'].loc[df['header']>0].astype('float'), facecolor='FireBrick',alpha=0.9,interpolate=False,label='IMMA1 in C3S',zorder=1)
#    for vari in df.columns[2:]:
#        ax.plot(df.loc[df[vari]>0].index,df[vari].loc[df[vari]>0],color=vars_color.get(vari),marker='o',markersize=1,linewidth=1)
#    
#    
#    ax.grid(linestyle=":",color='grey')
#    ax.set_yscale("log")
#    ax.set_ylabel('counts', color='k')
#    ax.set_xlim([xmin, xmax])
#    lines, labels = ax.get_legend_handles_labels()
#    ax.legend(lines[::-1],labels[::-1],loc='center',bbox_to_anchor=(0.5, -0.1),ncol=5)
#    plt.title(title)
#    
#    plt.tight_layout();
#    plt.savefig(out_path,bbox_inches='tight',dpi = 300)
#    
def plot_df_total():
    plt.rc('legend',**{'fontsize':font_size_legend})          # controls default text sizes
    plt.rc('axes', titlesize=axis_label_size)     # fontsize of the axes title
    plt.rc('axes', labelsize=axis_label_size)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=tick_label_size)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=tick_label_size)    # fontsize of the tick labels
    plt.rc('figure', titlesize=title_label_size)  # fontsize of the figure title
    
    n_shades = 2
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize, dpi=150) 
    ax.fill_between(df.index,0,df['ICOADS'].astype('float'), facecolor='DarkGrey',alpha=0.45,interpolate=False,label='ICOADS',zorder=1)
    ax.fill_between(df.index,0,df['header'].astype('float'), facecolor='FireBrick',alpha=0.9,interpolate=False,label='Total reports in C3S',zorder=1)
#    s_add_b = ingest_df['header'].loc[ingest_df['header']>0].astype('float') + buoys_df['header'].loc[buoys_df['header']>0].astype('float') # just to make sure as in total!
#    ax.fill_between(ingest_df.loc[ingest_df['header']>0].index,ingest_df['header'].loc[ingest_df['header']>0].astype('float'),s_add_b, facecolor='DarkSlateGrey',alpha=0.9,interpolate=False,label='Buoy reports in C3S',zorder=1)
    #ax.plot(df.loc[df['header']>0].index,df['header'].loc[df['header']>0],color='Black',marker='o',markersize=1,linewidth=1)
    for table in columns_no:
        if table == 'header':
            continue
        vari = table.split('-')[1]
        ax.plot(df.index,df[table],color=vars_color.get(vari),marker='o',markersize=1,linewidth=1)
    
    
    ax.grid(linestyle=":",color='grey')
    ax.set_yscale("log")
    ax.set_ylabel('counts', color='k')
    ax.set_xlim([xmin, xmax])
    lines, labels = ax.get_legend_handles_labels()
    legend1 = plt.legend(lines[-n_shades:],labels[-n_shades:],loc='center',bbox_to_anchor=(0.5, -0.1),ncol=3)
    legend2 = plt.legend(lines[0:-n_shades],labels[0:-n_shades],bbox_to_anchor=(0.005, 0.98),ncol=1,loc='upper left')
    plt.gca().add_artist(legend1)
    plt.gca().add_artist(legend2)
#    ax.legend(lines[::-1],labels[::-1],loc='center',bbox_to_anchor=(0.5, -0.1),ncol=5)
    #ax.legend(lines[::-1],labels[::-1],loc='center',bbox_to_anchor=(1, -0.1),ncol=5)
    plt.title(title)
    
    plt.tight_layout();
    plt.savefig(out_path,bbox_inches='tight',dpi = 300,transparent=True) 
    
##from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
#
#
#def plot_logbar():    
#    plt.rc('legend',**{'fontsize':font_size_legend})          # controls default text sizes
#    plt.rc('axes', titlesize=axis_label_size)     # fontsize of the axes title
#    plt.rc('axes', labelsize=axis_label_size)    # fontsize of the x and y labels
#    plt.rc('xtick', labelsize=tick_label_size)    # fontsize of the tick labels
#    plt.rc('ytick', labelsize=tick_label_size)    # fontsize of the tick labels
#    plt.rc('figure', titlesize=title_label_size)  # fontsize of the figure title
#    width = 1
#    fig = plt.figure(figsize=figsize, dpi=100)
#    ax = fig.add_subplot(111)
#    ax.set_xticklabels(ax.get_xticklabels(), rotation=75, fontsize = axis_label_size)
#    
#    iwidth = width
#    for dat,leg,col in zip(data,legend,color):
#        ax.bar( range(len(dat)),dat,tick_label=names,label=leg,color=col, log=True,width=iwidth,alpha=0.9,edgecolor='Black')
#        #iwidth=iwidth-0.1*width
#    ax.set_title(title)
#    ax.grid(which='major', axis='y', color='grey', linestyle=':', linewidth=1) 
#    ax.set_yscale('log')
#    ax.set_ylabel(ylabel)
#    ax.set_axisbelow(True)
#    plt.title(title)
#    ax.legend(bbox_to_anchor=(0.005, 0.98),ncol=1,loc='upper left')
#    plt.tight_layout()
#    plt.savefig(out_path,bbox_inches='tight',dpi = 300,transparent=True)
#    
# END FUNCTIONS ===============================================================   
#
#    
## MAIN ========================================================================
#
## 1. Read in data and adddddd: do rejects and ingests apart. Also keep buoys apart
#ingest_files=glob.glob(os.path.join(ingest_dir,'*.csv'))
#buoys_files = [x for x in ingest_files if buoys in x]
#reject_files=glob.glob(os.path.join(reject_dir,'*.csv'))
#
#deck_sid_ingest = [ os.path.basename(x)[0:7] for x in ingest_files ]
#
#for b in buoys_files:
#    ingest_files.remove(b)
#
#cols=['imma','header','sst','at','slp','wd','ws','wbt','dpt']
#deck_sid_df = pd.DataFrame(index=deck_sid_ingest,columns=['sid','deck','imma','header'])
#ingest_df = pd.DataFrame(index = pd.date_range(start = datetime.datetime(1981,1,1),end = datetime.datetime(2010,12,1),freq='MS'),columns=cols)
#reject_df = pd.DataFrame(index = pd.date_range(start = datetime.datetime(1981,1,1),end = datetime.datetime(2010,12,1),freq='MS'),columns=cols)
#buoys_df = pd.DataFrame(index = pd.date_range(start = datetime.datetime(1981,1,1),end = datetime.datetime(2010,12,1),freq='MS'),columns=cols)
#
#for fil in ingest_files:
#    deck_sid = os.path.basename(fil)[0:7] 
#    data_df = read_data()
#    ingest_df = ingest_df.add(data_df, fill_value=0)
#    deck_sid_df['imma'].loc[deck_sid] = data_df['imma'].sum()
#    deck_sid_df['header'].loc[deck_sid] = data_df['header'].sum()
#    deck_sid_df['sid'].loc[deck_sid] = deck_sid[0:3]
#    deck_sid_df['deck'].loc[deck_sid] = deck_sid[4:]
#    
#for fil in buoys_files:
#    deck_sid = os.path.basename(fil)[0:7] 
#    data_df = read_data()
#    buoys_df = buoys_df.add(data_df, fill_value=0)
#    deck_sid_df['imma'].loc[deck_sid] = data_df['imma'].sum()
#    deck_sid_df['header'].loc[deck_sid] = data_df['header'].sum()
#    
#for fil in reject_files:
#    data_df = read_data()
#    reject_df = reject_df.add(data_df, fill_value=0)
#    
#total_ingested = buoys_df.add(ingest_df, fill_value=0)
## 3. Plot
#deck_sid_df.sort_values(['deck','sid'],inplace=True)
#xmin = datetime.datetime(1981,1,1) - datetime.timedelta(days=15)
#xmax = datetime.datetime(2010,12,1) + datetime.timedelta(days=15)
#
#df=ingest_df
#title='Ship reports integrated in CDS \n Beta release Dec 2018 '
#out_path=os.path.join(indir,'total_ship_reports')
#plot_df()
#
#df=buoys_df
#title='Buoy reports integrated in CDS \n Beta release Dec 2018 '
#out_path=os.path.join(indir,'total_buoy_reports')
#plot_df()
#
#df=total_ingested
#title='Marine reports integrated in CDS \n Beta release Dec 2018 '
#out_path=os.path.join(indir,'total_reports')
#plot_df_total()
#
#
#names = deck_sid_df.index.values
#data = [deck_sid_df['imma'],deck_sid_df['header']]
#legend = ['Initial','In CDS']
#color = ['DarkGrey','FireBrick']
#title = ''
#ylabel = 'Number of reports'
#out_path=os.path.join(indir,'reports_by_sid-deck')
#title='ICOADS 1981-2010 selection \n Beta release Dec 2018 '
#plot_logbar()


filename_field_sep = '-'
 
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
try:
    data_path = sys.argv[1]
    release = sys.argv[2]
    update = sys.argv[3]
    source = sys.argv[4]
    yr_ini = sys.argv[5]
    yr_end = sys.argv[6]
except Exception as e:
    logging.error(e, exc_info=True)
    sys.exit(1)
 

level='level2'
paths = {}
paths[level] = os.path.join(data_path,release,source,level)
paths['reports'] = os.path.join(data_path,release,source,level,'reports')

level2_list = os.path.join(paths.get(level),filename_field_sep.join([release,update,'selection.json']))

with open(level2_list,'r') as fileObj:
    include_dict = json.load(fileObj)

include_list = list(include_dict.keys())
include_list.remove('params_exclude')

# Initialize the structure where the TSs is stored
# in io_history: yr-mo|ICOADS|PT selection|l1c-invalid|md-invalid|dt-invalid|id-invalid|invalid|valid|C3S
# in no_reports: yr-mo|header|observations-at|observations-sst|observations-dpt|observations-slp|observations-ws|observations-wd
columns_no = ['header','observations-at','observations-sst','observations-dpt','observations-slp','observations-ws','observations-wd']
columns_io = ['ICOADS','PT selection','l1c-invalid','md-invalid','dt-invalid','id-invalid','invalid','valid','C3S']
columns = columns_no + columns_io
index = pd.date_range(start=datetime.datetime(int(yr_ini),1,1),end=datetime.datetime(int(yr_end),12,1),freq='MS')
all_df = pd.DataFrame(index=index,columns = columns)
best_df = pd.DataFrame(index=index,columns = columns)

for sid_dck in include_list:
    logging.info('Including sid_dck {}'.format(sid_dck))
    no_best_file = os.path.join(paths.get('reports'),sid_dck, '-'.join(['no_reports',release,update,'qcr0-qc0-ts.psv']))
    no_all_file = os.path.join(paths.get('reports'),sid_dck, '-'.join(['no_reports',release,update,'all-ts.psv']))
    io_file = os.path.join(paths.get('reports'),sid_dck, '-'.join(['io_history',release,update,'ts.psv']))
    file_paths = [no_best_file,no_all_file,io_file]
    if any([ not os.path.isfile(x) for x in file_paths ]):
        logging.error('Could not find data paths: {}'.format(','.join([ x for x in file_paths if not os.path.isfile(x)])))
        continue
    no_all_dfi = pd.read_csv(no_all_file,sep='|',parse_dates=['yr-mo'])
    no_best_dfi = pd.read_csv(no_best_file,sep='|',parse_dates=['yr-mo'])
    io_dfi = pd.read_csv(io_file,sep='|',parse_dates=['yr-mo'])
    
    no_all_dfi.set_index('yr-mo',drop=True,inplace=True)
    no_best_dfi.set_index('yr-mo',drop=True,inplace=True)
    io_dfi.set_index('yr-mo',drop=True,inplace=True)
    
    all_df = all_df.add(no_all_dfi,fill_value=0)
    all_df = all_df.add(io_dfi,fill_value=0)
    best_df = best_df.add(no_best_dfi,fill_value=0)
    best_df = best_df.add(io_dfi,fill_value=0)

all_df.replace(0,np.nan,inplace=True)
best_df.replace(0,np.nan,inplace=True)
  
xmin = datetime.datetime(int(yr_ini),1,1) - datetime.timedelta(days=15)
xmax = datetime.datetime(int(yr_end),12,1) + datetime.timedelta(days=15)
  
df = best_df
title='Marine reports integrated in CDS \n Release1 - Sept 2019. Optimal quality setting '
out_path = os.path.join(paths.get('reports'),'-'.join(['no_reports',release,update,'qcr0-qc0-ts.png']))
plot_df_total()

df = all_df
title='Marine reports integrated in CDS \n Release1 - Sept 2019. All qualities '
out_path = os.path.join(paths.get('reports'),'-'.join(['no_reports',release,update,'all-ts.png']))
plot_df_total()