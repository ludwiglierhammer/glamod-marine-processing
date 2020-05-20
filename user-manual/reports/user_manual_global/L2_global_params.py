#!/usr/bin/env python3
#
#  Needs to run with py env2: bwcause of pandas to_parquet (different to dask to parquet!)
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 09:24:24 2020

@author: iregon
"""
import os
import sys
import glob
import json
import pandas as pd
import numpy as np
import cdm

from dask import dataframe as dd
import dask.diagnostics as diag
import datashader as ds
from datashader.geo import lnglat_to_meters
import datashader.transfer_functions as tf
import xarray as xr
import shutil
import cartopy.crs as ccrs
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import datetime


try:
    param = sys.argv[1]
except:
    param = 'slp'
    print('SETTING HARCODED OBSERVED PARAMETER: {}'.format(param))
    print('To change it, give it as COMMAND LINE ARGUMENT TO THIS SCRIPT')
    pass
    

region = 'Global'
resolution = 'lo_res'

release = 'r092019'
update = '000000'
release_init = 1950
release_end = 2010

level2_config_path = '/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/r092019_000000/ICOADS_R3.0.0T/L2_config.json' 
#level2_config_path = '/Users/iregon/C3S/Release_092019/UserManual/L2_config.json' 
level2_path = os.path.dirname(level2_config_path)

level2_data_path = '/group_workspaces/jasmin2/glamod_marine/data/r092019/ICOADS_R3.0.0T/level2'
#level2_data_path = '/Users/iregon/dessaps/test_data/level2'

level2_reports_path  = os.path.join(level2_data_path,'reports')
#level2_reports_path  = level2_path

# Some plotting options
font_size_legend = 13
axis_label_size = 14
tick_label_size = 12
title_label_size = 16
markersize = 2
figsize_ts=(20, 4)
    
plt.rc('legend',**{'fontsize':font_size_legend})        # controls default text sizes
plt.rc('axes', titlesize=axis_label_size)     # fontsize of the axes title
plt.rc('axes', labelsize=axis_label_size)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('ytick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('figure', titlesize=title_label_size)  # fontsize of the figure title

coastline_width = 1
grid_width = 0.7
grid_label_size = 12
colorbar_title_size = 14
colorbar_label_size = 12
grid_label_size_mosaic = 6
colorbar_title_size_mosaic = 9
colorbar_label_size_mosaic = 7
coastline_width_mosaic = 0.3

# PARAMETER PLOTTING PROPERTIES
script_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(script_path,'var_properties.json'),'r') as f:
    var_properties = json.load(f)

var_properties['saturation']['slp'] = [950,1040]
var_properties['saturation']['at'] = [-10,40]
var_properties['saturation']['dpt'] = [-10,40]
var_properties['saturation']['wbt'] = [-10,40]
var_properties['saturation']['ws'] = [0,20]

CDM_DTYPES = {'latitude':'float32','longitude':'float32','report_timestamp':'object','report_quality':'int8',
              'observation_value':'float32','date_time':'object','sensor_id':'object',
              'quality_flag':'int8','report_id':'object'}
READ_COLS = ['report_id','latitude','longitude','report_quality','report_timestamp']
READ_COLS_PARAM = ['report_id','observation_value','quality_flag','date_time']

CDM_COLS = list(set(READ_COLS + READ_COLS_PARAM))
CDM_COLS.remove('report_timestamp')
dtypes_cdm_table = { x:CDM_DTYPES.get(x) for x in CDM_COLS }

REGIONS = dict()
REGIONS['Global'] = ((-180.00, 180.00), (-90.00, 90.00))
REGIONS['North_Atlantic']   = (( -90.00,  10.00), ( 0, 80))
DEGREE_FACTOR_RESOLUTION = dict()
DEGREE_FACTOR_RESOLUTION['lo_res'] = 1
DEGREE_FACTOR_RESOLUTION['me_res'] = 2
DEGREE_FACTOR_RESOLUTION['hi_res'] = 5


ENCODINGS = {'latitude': {'dtype': 'int16', 'scale_factor': 0.01, '_FillValue': -99999},
             'longitude': {'dtype': 'int16', 'scale_factor': 0.01, '_FillValue': -99999},
             'counts': {'dtype': 'int64','_FillValue': -99999}}


def map_to_file():
    # HOW ARE WE PLOTTING:
    # We plot using matplotlib (not xarray direct plotting) on a cartopy axis
    # Have to do some adjustments to matplotlib because of cartopy.
    # Why cartopy, and not basemap?:   https://github.com/SciTools/cartopy/issues/920
    # But we might face the need of a projection not yet in cartopy......
    proj = ccrs.PlateCarree()
    kwargs = {}
    kwargs['colorbar_w'] = 4
    kwargs['grid_label_size'] = grid_label_size
    kwargs['colorbar_label_size'] = colorbar_label_size
    kwargs['colorbar_title_size'] = colorbar_title_size
    kwargs['show_colorbar'] = True
    kwargs['colormap'] = colormap
    kwargs['colorbar_title'] = cbar_title
    kwargs['colorbar_orien'] = 'v'
    kwargs['coastline_width'] = coastline_width
    
    if logVal:     
        min_value = 1; max_value = dataset.max()
        z = dataset.where(dataset> 0).values
        normalization = LogNorm(vmin=min_value, vmax=max_value)
    else:
        z = dataset #.where(dataset> 0).values
        min_value = var_properties['saturation'].get(param)[0] 
        max_value = var_properties['saturation'].get(param)[1]

        normalization = mpl.colors.Normalize(vmin=min_value, vmax=max_value)
          
    plt.title(title)# + "-".join([str(y_ini),str(y_end)]) + ' composite')
    f, ax = plt.subplots(1, 1, subplot_kw=dict(projection=proj),figsize=(14,7),dpi = 150)  # It is important to try to estimate dimensions that are more or less proportional to the layout of the mosaic....
    lons = dataset['longitude']
    lats = dataset['latitude']
    
    
    ax.pcolormesh(lons,lats,z,transform=ccrs.PlateCarree(),cmap = colormap, vmin = min_value , vmax = max_value,norm=normalization )
    gl = ax.gridlines(crs=ccrs.PlateCarree(),color = 'k', linestyle = ':', linewidth = grid_width, alpha=0.3, draw_labels=True)
    ax.coastlines(linewidth = coastline_width)
    gl.xlabels_bottom = False
    gl.ylabels_right = False
    gl.xlabel_style = {'size': grid_label_size}
    gl.ylabel_style = {'size': grid_label_size}
    # following https://matplotlib.org/2.0.2/mpl_toolkits/axes_grid/users/overview.html#colorbar-whose-height-or-width-in-sync-with-the-master-axes
    # we need to set axes_class=plt.Axes, else it attempts to create
    # a GeoAxes as colorbar
    divider = make_axes_locatable(ax)
    new_axis_w = str(kwargs['colorbar_w']) + '%'
    if orientation == 'vertical':
        cax = divider.new_horizontal(size = new_axis_w, pad = 0.08, axes_class=plt.Axes)
    else:
        cax = divider.new_vertical(size = new_axis_w, pad = 0.08, axes_class=plt.Axes,pack_start=True)
    f.add_axes(cax)
    if show_colorbar:
        #cb_v = plt.colorbar(t1, cax=cax) could do it this way and would work: would just have to add label and tick as 2 last lines below. But would have to do arrangements anyway if we wanted it to be horizontal. So we keep as it is...
        cb = mpl.colorbar.ColorbarBase(cax, cmap=colormap,norm = normalization, orientation=orientation)
        cb.set_label(cbar_title, size = colorbar_title_size)
        cb.ax.tick_params(labelsize = colorbar_label_size)
    else:
        cax.axis('off')

    plt.savefig(out_file,bbox_inches='tight')
    plt.close()


def plot_grid_ts():
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize_ts, dpi=150)
    mon_index = pd.date_range(start=datetime.datetime(release_init,1,1),end=datetime.datetime(release_end,12,1),freq='MS')
    
    ncells_df = ncells_agg_qc0.to_dataframe()
    ncells_df = ncells_df.reindex(mon_index)
    ncells_index = ncells_df.index
    
    mean_df = var_properties['offset'].get(param) + var_properties['scale'].get(param)*mean_agg_qc0.mean(dim = ['latitude','longitude']).to_dataframe()
    mean_df = mean_df.reindex(mon_index)
    mean_df_index = mean_df.index
    
    ax.bar(ncells_index,ncells_df['counts'],color ='SlateGray',alpha = 0.7,width = [(ncells_index[j+1]-ncells_index[j]).days for j in range(len(ncells_index)-1)] + [30],label = 'no.cells')
    #ax2 = ax.twinx() 
    
    #ax2.plot(mean_df_index,mean_df['mean'],color = 'red',linewidth = 1, label = var_properties['short_name_upper'].get(param))
    
    ax.set_xlim([mon_index[0], mon_index[-1]])
    
    ax.set_ylabel('No. 1x1 grid cells', color='k')
    #ax2.set_ylabel('Mean ' + var_properties['short_name_upper'].get(param) + ' (' + var_properties['units'].get(param) + ')', color='k')
    ax.grid(linestyle=':',which='major')
    ax.title.set_text(title)
    plt.legend()
    plt.savefig(fig_path,bbox_inches='tight',dpi = 300)
    plt.close(fig)


    return

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
    if qc == True:
        return canvas.points(cdm_table.loc[(cdm_table['report_quality']==0) & (cdm_table['quality_flag'] == 0)],'longitude','latitude',ds.count('report_quality'))     
    else:
        return canvas.points(cdm_table,'longitude','latitude',ds.count('report_quality'))      

def aggs_value(qc = False):
#    if qc:
#        month_par = df.get_partition(i)
#        month_data = month_par.loc[month_par['quality_flag']==0].compute()
#    else:
#        month_data = df.get_partition(i).compute()
    if qc == True:
        return canvas.points(cdm_table.loc[(cdm_table['report_quality']==0) & (cdm_table['quality_flag'] == 0)],'longitude','latitude',ds.mean('observation_value'))     
    else:
        return canvas.points(cdm_table,'longitude','latitude',ds.mean('observation_value'))

# MAIN ------------------------------------------------------------------------    
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


# READ DATA
obs_table = 'observations-' + param
level2_files = []

for sid_dck in level2_list:
    level2_files.extend(glob.glob(os.path.join(level2_data_path,sid_dck,obs_table + '*.psv' )))

level2_ym = list(set([ '-'.join(os.path.basename(x).split('-')[2:4]) for x in level2_files ]))
level2_ym.sort()
level2_months = pd.to_datetime(level2_ym,format='%Y-%m')

canvas = create_canvas(REGIONS.get(region),DEGREE_FACTOR_RESOLUTION.get(resolution))
# CREATE THE MONTHLY STATS ON THE DF PARTITIONS
nreports_list_qc0 = []
ncells_list_qc0 = []
mean_list_qc0 = []

for ym in level2_months:
    print(ym)
    parq_path = os.path.join(level2_reports_path,param + '.data.parq.tmp')
    date_file = ym.strftime('%Y-%m')
    param_files = glob.glob(os.path.join(level2_data_path,'*','-'.join([obs_table,date_file]) + '*.psv' ))
    param_paths = [ os.path.dirname(x) for x in param_files ]
    cdm_table_ym = pd.DataFrame()
    for i,param_path in enumerate(param_paths):
        print(os.path.basename(param_path))
        cdm_table = cdm.read_tables(param_path,'-'.join([date_file,release,update]),cdm_subset = ['header',obs_table],col_subset = {'header':READ_COLS,obs_table:READ_COLS_PARAM})
        cdm_table.dropna(inplace = True)
        cdm_table.drop(columns=[[obs_table, 'report_id'],['header','report_timestamp']],inplace = True)
        cdm_table.columns = cdm_table.columns.droplevel(0)
        # This is because the cdm module treats them as plain objects
        cdm_table = cdm_table.astype(dtypes_cdm_table)
        cdm_table_ym = pd.concat([cdm_table_ym,cdm_table], sort = False)
    # SAVE TO PARQUET AND READ DF BACK FROM THAT TO ENHANCE PERFORMANCE
    # CHECK HERE NUMBER OF RECORDS AFTER AND BEFORE SAVING, ETC....
    print('to parquet')
    with diag.ProgressBar(), diag.Profiler() as prof, diag.ResourceProfiler(0.5) as rprof:
        append = False if i == 0 else True
        #cdm_table.to_parquet(parq_path, engine = 'pyarrow',mode='a')#, compression = 'gzip', append = append)
        #cdm_table_ym.to_parquet(parq_path, engine = 'fastparquet', compression = 'gzip', append = append)
        cdm_table_ym.to_parquet(parq_path, engine = 'fastparquet', compression = 'gzip',append = False)  
    del cdm_table_ym
        
    print('From parquet')
    cdm_table = dd.read_parquet(parq_path)
    
    nreports_arr_qc0 = aggs_counts(qc = True).assign_coords(time=ym).rename('counts')
    mean_arr_qc0 = aggs_value(qc = True).assign_coords(time=ym).rename('mean')
    nreports_list_qc0.append(nreports_arr_qc0)
    mean_list_qc0.append(mean_arr_qc0)
    ncells_list_qc0.append(nreports_arr_qc0.where(nreports_arr_qc0 > 0).count())

#    Now this seems different with pandas to parquet, is it the engine choice?
#    shutil.rm(parq_path)
    os.remove(parq_path)

    
nreports_agg_qc0 = xr.concat(nreports_list_qc0,dim = 'time')
ncells_agg_qc0 = xr.concat(ncells_list_qc0,dim = 'time')
mean_agg_qc0 = xr.concat(mean_list_qc0,dim = 'time')

total_reports_qc0 = nreports_agg_qc0.sum(dim = 'time')
mean_qc0 = mean_agg_qc0.mean(dim = 'time')


#out_file = os.path.join(level2_reports_path,'global_no_reports_map_qc0.nc')
#nreports_agg_qc0.encoding = ENCODINGS 
#nreports_agg_qc0.to_netcdf(out_file,encoding = ENCODINGS,mode='w')
#
show_colorbar = True
orientation = 'horizontal'

dataset = total_reports_qc0
logVal = True
title = 'N per grid'
cbar_title = var_properties['short_name_upper'].get(param) + ' no.reports'
colormap = plt.get_cmap('viridis')
#colormap = plt.get_cmap(var_properties['colormap'].get(param))
out_file = os.path.join(level2_reports_path,'global_no_reports_map_' + param + '_qc0.jpg')
map_to_file()


param_offset = var_properties['offset'].get(param)
param_scale = var_properties['scale'].get(param)
dataset = param_offset + param_scale*mean_qc0
logVal = False
title = 'N per grid'
cbar_title = var_properties['short_name_upper'].get(param) + ' mean (' + var_properties['units'].get(param) + ')'
colormap = plt.get_cmap(var_properties['colormap'].get(param))
out_file = os.path.join(level2_reports_path,'global_mean_map_' + param + '_qc0.jpg')
map_to_file()

title = var_properties['short_name_upper'].get(param) + ': spatial coverage'
fig_path = os.path.join(level2_reports_path,'global_grid_counts_ts_' + param + '_qc0.jpg')
plot_grid_ts()
#
