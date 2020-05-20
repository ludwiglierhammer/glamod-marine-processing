#!/usr/bin/env python3
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




region = 'Global'
resolution = 'lo_res'


level2_config_path = '/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/r092019_000000/ICOADS_R3.0.0T/L2_config.json' 
level2_path = os.path.dirname(level2_config_path)

level2_data_path = '/group_workspaces/jasmin2/glamod_marine/data/r092019/ICOADS_R3.0.0T/level2'
level2_reports_path  = os.path.join(level2_data_path,'reports')

# Some plotting options
font_size_legend = 11
axis_label_size = 11
tick_label_size = 9
title_label_size = 14
markersize = 2
figsize=(9, 14)
    
plt.rc('legend',**{'fontsize':font_size_legend})        # controls default text sizes
plt.rc('axes', titlesize=axis_label_size)     # fontsize of the axes title
plt.rc('axes', labelsize=axis_label_size)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('ytick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('figure', titlesize=title_label_size)  # fontsize of the figure title

coastline_width = 1
grid_width = 0.7
grid_label_size = 12
colorbar_title_size = 11
colorbar_label_size = 12
grid_label_size_mosaic = 6
colorbar_title_size_mosaic = 9
colorbar_label_size_mosaic = 7
coastline_width_mosaic = 0.3


colormap = plt.get_cmap('viridis')


CDM_DTYPES = {'latitude':'float32','longitude':'float32','report_timestamp':'object','report_quality':'int8',
              'observation_value':'float32','date_time':'object','sensor_id':'object',
              'quality_flag':'int8','report_id':'object'}
READ_COLS = ['latitude','longitude','report_quality','report_timestamp']
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



param_ordered = ['AT','SST','DPT','WBT','SLP','WD','WS']

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
        z = dataset.where(dataset> 0).values
        min_value = 1 
        max_value = np.nanmax(dataset.max())
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
        print('adding_colorbar')
        cb = mpl.colorbar.ColorbarBase(cax, cmap=colormap,norm = normalization, orientation=orientation)
        cb.set_label(cbar_title, size = colorbar_title_size)
        print('adding_colorbar2')
        cb.ax.tick_params(labelsize = colorbar_label_size)
        print('adding_colorbar3')
    else:
        cax.axis('off')

    plt.savefig(out_file,bbox_inches='tight')
    plt.close()


def bounds(x_range, y_range):
    return dict(x_range=x_range, y_range=y_range)


def create_canvas(bbox,degree_factor):
    plot_width = int(abs(bbox[0][0]-bbox[0][1])*degree_factor)
    plot_height = int(abs(bbox[1][0]-bbox[1][1])*degree_factor)    
    return ds.Canvas(plot_width=plot_width, plot_height=plot_height, **bounds(*bbox))
    
def aggs(qc = False):
#    if qc:
#        month_par = df.get_partition(i)
#        month_data = month_par.loc[month_par['quality_flag']==0].compute()
#    else:
#        month_data = df.get_partition(i).compute()
    if qc == True:
        return canvas.points(df.loc[df['report_quality']==0],'longitude','latitude',ds.count('report_quality'))     
    else:
        return canvas.points(df,'longitude','latitude',ds.count('report_quality'))      

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
level2_files = []

for sid_dck in level2_list:
    level2_files.extend(glob.glob(os.path.join(level2_data_path,sid_dck,'header-*.psv' )))

level2_ym = list(set([ '-'.join(os.path.basename(x).split('-')[1:3]) for x in level2_files ]))
level2_ym.sort()
level2_months = pd.to_datetime(level2_ym,format='%Y-%m')

print(level2_files)

dtypes = { x:CDM_DTYPES.get(x) for x in READ_COLS }
canvas = create_canvas(REGIONS.get(region),DEGREE_FACTOR_RESOLUTION.get(resolution))
# CREATE THE MONTHLY STATS ON THE DF PARTITIONS
nmonths_list_qc0 = []
nreports_list_qc0 = []
nmonths_list = []
nreports_list = []

for ym in level2_months:
    print(ym)   
    data_files = glob.glob(os.path.join(level2_data_path,'*','header-' + ym.strftime('%Y-%m') + '*.psv' ))
    df = dd.read_csv(data_files,delimiter='|',usecols = READ_COLS,parse_dates=['report_timestamp'],dtype=dtypes)    
    print(data_files)
    # SAVE TO PARQUET AND READ DF BACK FROM THAT TO ENHANCE PERFORMANCE
    # CHECK HERE NUMBER OF RECORDS AFTER AND BEFORE SAVING, ETC....
    print('to parquet')
    parq_path = os.path.join(level2_reports_path,'data.parq.tmp')
    with diag.ProgressBar(), diag.Profiler() as prof, diag.ResourceProfiler(0.5) as rprof:
        df.to_parquet(parq_path)
        
    del df
    print('From parquet')
    df = dd.read_parquet(parq_path)
    nreports_arr_qc0 = aggs(qc = True).assign_coords(time=ym).rename('counts')
    nreports_list_qc0.append(nreports_arr_qc0)
    nmonths_list_qc0.append(nreports_arr_qc0 >0)
    nreports_arr = aggs(qc = False).assign_coords(time=ym).rename('counts')
    nreports_list.append(nreports_arr)
    nmonths_list.append(nreports_arr>0)
    shutil.rmtree(parq_path)

nreports_agg = xr.concat(nreports_list,dim = 'time')
nmonths_agg = xr.concat(nmonths_list,dim = 'time')
    
nreports_agg_qc0 = xr.concat(nreports_list_qc0,dim = 'time')
nmonths_agg_qc0 = xr.concat(nmonths_list_qc0,dim = 'time')

total_reports = nreports_agg.sum(dim = 'time')
total_nmonths = nmonths_agg.sum(dim = 'time')

out_file = os.path.join(level2_reports_path,'global_no_months_map_all.nc')
nmonths_agg.encoding = ENCODINGS 
nmonths_agg.to_netcdf(out_file,encoding = ENCODINGS,mode='w')

out_file = os.path.join(level2_reports_path,'global_no_reports_map_all.nc')
nreports_agg.encoding = ENCODINGS 
nreports_agg.to_netcdf(out_file,encoding = ENCODINGS,mode='w')

total_reports_qc0 = nreports_agg_qc0.sum(dim = 'time')
total_nmonths_qc0 = nmonths_agg_qc0.sum(dim = 'time')

out_file = os.path.join(level2_reports_path,'global_no_months_map_qc0.nc')
nmonths_agg_qc0.encoding = ENCODINGS 
nmonths_agg_qc0.to_netcdf(out_file,encoding = ENCODINGS,mode='w')

out_file = os.path.join(level2_reports_path,'global_no_reports_map_qc0.nc')
nreports_agg_qc0.encoding = ENCODINGS 
nreports_agg_qc0.to_netcdf(out_file,encoding = ENCODINGS,mode='w')

show_colorbar = True
orientation = 'horizontal'

dataset = total_nmonths_qc0
logVal = True
title = 'N per grid'
cbar_title = 'no.months'
out_file = os.path.join(level2_reports_path,'global_no_months_map_qc0.jpg')
print('months')
map_to_file()

dataset = total_reports_qc0
logVal = True
title = 'N per grid'
cbar_title = 'no.reports'
out_file = os.path.join(level2_reports_path,'global_no_reports_map_qc0.jpg')
print('reports')
map_to_file()
    

dataset = total_nmonths
logVal = True
title = 'N per grid'
cbar_title = 'no.months'
out_file = os.path.join(level2_reports_path,'global_no_months_map_all.jpg')
print('months')
map_to_file()

dataset = total_reports
logVal = True
title = 'N per grid'
cbar_title = 'no.reports'
out_file = os.path.join(level2_reports_path,'global_no_reports_map_all.jpg')
print('reports')
map_to_file()

