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


def map_to_file():
    # HOW ARE WE PLOTTING:
    # We plot using matplotlib (not xarray direct plotting) on a cartopy axis
    # Have to do some adjustments to matplotlib because of cartopy.
    # Why cartopy, and not basemap?:   https://github.com/SciTools/cartopy/issues/920
    # But we might face the need of a projection not yet in cartopy......
    proj = ccrs.Robinson()
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
        min_value = 1;
        max_value = dataset.max();
        z = dataset.where(dataset > 0).values
        normalization = LogNorm(vmin=min_value, vmax=max_value)
    else:
        z = dataset.where(dataset> 0).values
        min_value = 1 
        max_value = np.nanmax(dataset.max())
        normalization = mpl.colors.Normalize(vmin=min_value, vmax=max_value)
          
    f, ax = plt.subplots(1, 1, subplot_kw=dict(projection=proj),figsize=(14,7),dpi = 150)  # It is important to try to estimate dimensions that are more or less proportional to the layout of the mosaic....
    lons = dataset['longitude'].values
    lats = dataset['latitude'].values
    
    ax.set_title(title, fontdict={'fontweight' :'semibold'}, loc='center',pad = 10.,color='DimGray') 
    #ax.stock_img()
    ax.pcolormesh(lons,lats,z,transform=ccrs.PlateCarree(),cmap = colormap, vmin = min_value , vmax = max_value,norm=normalization )
    gl = ax.gridlines(crs=ccrs.PlateCarree(), linestyle = ':', linewidth = grid_width, alpha=0.7,color='k', draw_labels=False)
    ax.coastlines(linewidth = coastline_width)
    #gl.xlabels_bottom = False
    #gl.ylabels_right = False
    #gl.xlabel_style = {'size': grid_label_size}
    #gl.ylabel_style = {'size': grid_label_size}
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
    plt.savefig(out_file,bbox_inches='tight',transparent=True)
    plt.close()



# Some plotting options
font_size_legend = 11
axis_label_size = 11
tick_label_size = 9
title_label_size = 16
markersize = 2
figsize=(9, 14)

plt.rc('legend',**{'fontsize':font_size_legend})        # controls default text sizes
plt.rc('axes', titlesize=30)     # fontsize of the axes title
plt.rc('axes', labelsize=axis_label_size)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('ytick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('figure', titlesize=title_label_size)  # fontsize of the figure title

coastline_width = 1
grid_width = 0.7
grid_label_size = 12
colorbar_title_size = 24
colorbar_label_size = 26
grid_label_size_mosaic = 6
colorbar_title_size_mosaic = 9
colorbar_label_size_mosaic = 7
coastline_width_mosaic = 0.3


colormap = plt.get_cmap('viridis')

show_colorbar = True
orientation = 'horizontal'

nc_file = '/group_workspaces/jasmin2/glamod_marine/data/r092019/ICOADS_R3.0.0T/level2_lite_20200210/reports/global_no_months_map_qc0.nc'
level2_path = os.path.dirname(nc_file)

dataset_monthly = xr.open_dataarray(nc_file)
dataset = dataset_monthly.sum(dim = 'time')
logVal = True # False
title = 'Temporal coverage of marine reports'
cbar_title = 'Number of months with at least one report'
out_file = os.path.join(level2_path,'global_no_months_map_qc0_robinson_viridis_title_noland.jpg')
print('months')
map_to_file()

nc_file = '/group_workspaces/jasmin2/glamod_marine/data/r092019/ICOADS_R3.0.0T/level2_lite_20200210/reports/global_no_reports_map_qc0.nc'
level2_path = os.path.dirname(nc_file)

dataset_monthly = xr.open_dataarray(nc_file)
dataset = dataset_monthly.sum(dim = 'time')
logVal = True # False
title = 'N per grid'
cbar_title = 'no.reports'
out_file = os.path.join(level2_path,'global_no_reports_map_qc0_robinson.pdf')
print('reports')
map_to_file()
