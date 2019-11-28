#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 20 11:43:22 2018


Modes:
    qcr0-qc0-um: this is the 'user recommended use' case
        data values: qcr0-qc0.nc
        axis: saturated to common max/min. Color? for those above saturation
    all: all data in C3S
        data values: .nc
        axis: unbounded
    qcr0-qc0: this is for QA purposes, to compare the effect of the parameter quality control
        data values: qcr0-qc0.nc
        data counts: total reports, unchecked quality report, failed quality report, failed param quality, passed param quality
        axis: unbounded
    qcr0: this is for QA purposes, to compare the effect of the parameter quality control
        data values: qcr0-qc0_qc1.nc
        axis: unbounded  


@author: iregon
"""
import os
import json
import sys
import glob
import logging
import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import matplotlib as mpl
import numpy as np

from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import xarray as xr
import cartopy.crs as ccrs


logging.getLogger('plt').setLevel(logging.INFO)
logging.getLogger('mpl').setLevel(logging.INFO)


script_path = os.path.dirname(os.path.realpath(__file__))
# PARAMS ----------------------------------------------------------------------

with open(os.path.join(script_path,'var_properties.json'),'r') as f:
    var_properties = json.load(f)
    
vdims = ['counts','max','min','mean']
mosaic_vdims = ['counts','min','max']
scalable_vdims = ['max','min','mean']
kdims = ['latitude', 'longitude']

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

vars_colormap = dict()
vars_colormap['sst'] = plt.get_cmap(var_properties['colormap'].get('sst'))
vars_colormap['at'] = plt.get_cmap(var_properties['colormap'].get('at'))
vars_colormap['slp'] = plt.get_cmap(var_properties['colormap'].get('slp'))
vars_colormap['wd'] = plt.get_cmap(var_properties['colormap'].get('wd'))
vars_colormap['ws'] = plt.get_cmap(var_properties['colormap'].get('ws'))
vars_colormap['dpt'] = plt.get_cmap(var_properties['colormap'].get('dpt'))
vars_colormap['wbt'] = plt.get_cmap(var_properties['colormap'].get('wbt'))
vars_colormap['counts'] = plt.get_cmap(var_properties['colormap'].get('counts'))
# END PARAMS ------------------------------------------------------------------

def map_on_subplot(f,subplot_ax,z,lons,lats,**kwargs):
    # Plots a map on subplot cartopy axis
    # The axis is divided (an map re-scaled accordingly) to accomodate a colorbar. Colorbar is only drawn if show_colorbar = True.
    # Otherwise, added axis is made transparent. This axis is always added to keep same scaling between maps in subplots.
    # This colorbar approach so that the colorbar height matches the height of cartopy's axes...!!!!!
    # colorbar_w = percent of axis width: have to declare equal to other subplots in figure so that re-scaling is the same
    #
    # To be used locally: all variables/params to be set in script before invocation (but subplot_axis)
    #
    # Could potentially, more or less easily, choose to have an horiontal colorbar...just a couple of parameters more....

    subplot_ax.pcolormesh(lons,lats,z,transform=ccrs.PlateCarree(),cmap = kwargs['colormap'], vmin = kwargs['min_value'] , vmax = kwargs['max_value'],norm=kwargs['normalization'] )
    gl = subplot_ax.gridlines(crs=ccrs.PlateCarree(),color = 'k', linestyle = ':', linewidth = grid_width, alpha=0.3, draw_labels=True)
    subplot_ax.coastlines(linewidth = kwargs['coastline_width'])
    gl.xlabels_bottom = False
    gl.ylabels_right = False
    gl.xlabel_style = {'size': kwargs['grid_label_size']}
    gl.ylabel_style = {'size': kwargs['grid_label_size']}
    # following https://matplotlib.org/2.0.2/mpl_toolkits/axes_grid/users/overview.html#colorbar-whose-height-or-width-in-sync-with-the-master-axes
    # we need to set axes_class=plt.Axes, else it attempts to create
    # a GeoAxes as colorbar
    divider = make_axes_locatable(subplot_ax)
    new_axis_w = str(kwargs['colorbar_w']) + '%'
    if kwargs['colorbar_orien'] == 'v':
        cax = divider.new_horizontal(size = new_axis_w, pad = 0.08, axes_class=plt.Axes)
        orientation = 'vertical'
    else:
        cax = divider.new_vertical(size = new_axis_w, pad = 0.08, axes_class=plt.Axes,pack_start=True)
        orientation = 'horizontal'
    f.add_axes(cax)
    if kwargs['show_colorbar']:
        #cb_v = plt.colorbar(t1, cax=cax) could do it this way and would work: would just have to add label and tick as 2 last lines below. But would have to do arrangements anyway if we wanted it to be horizontal. So we keep as it is...
        cb = mpl.colorbar.ColorbarBase(cax, cmap=kwargs['colormap'],norm = kwargs['normalization'], orientation=orientation, extend='both')
        cb.set_label(kwargs['colorbar_title'], size = kwargs['colorbar_title_size'])
        cb.ax.tick_params(labelsize = kwargs['colorbar_label_size'])
    else:
        cax.axis('off')


def map_individual(dataset,agg,param,out_file,max_value = None, min_value = None):
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
    kwargs['colormap'] = vars_colormap.get('counts')  if agg == 'counts' else vars_colormap.get(param)
    kwargs['colorbar_title'] = var_properties['units'].get('counts') if agg == 'counts' else agg + " (" + var_properties['units'].get(param) + ")"
    kwargs['colorbar_orien'] = 'v'
    kwargs['coastline_width'] = coastline_width
    
    if agg == 'counts':     
        kwargs['min_value'] = 1; kwargs['max_value'] = dataset['counts'].max()
        z = dataset[agg].where(dataset[agg]> 0).values
        kwargs['normalization'] = LogNorm(vmin=kwargs['min_value'], vmax=kwargs['max_value'])
    else:
        kwargs['min_value'] = np.nanmin(dataset[scalable_vdims].min().to_array()) if min_value is None else min_value
        kwargs['max_value'] = np.nanmax(dataset[scalable_vdims].max().to_array()) if max_value is None else max_value
        kwargs['normalization'] = mpl.colors.Normalize(vmin=kwargs['min_value'], vmax=kwargs['max_value'])
        z = dataset[agg].values
    plt.title('-'.join([param]) + ": " + " ".join([agg]) + '\n')# + "-".join([str(y_ini),str(y_end)]) + ' composite')
    f, ax = plt.subplots(1, 1, subplot_kw=dict(projection=proj),figsize=(14,7),dpi = 150)  # It is important to try to estimate dimensions that are more or less proportional to the layout of the mosaic....
    lons = dataset[agg]['longitude']
    lats = dataset[agg]['latitude']
    map_on_subplot(f,ax,z,lons,lats,**kwargs)
    plt.savefig(out_file,bbox_inches='tight')
    plt.close()

def map_mosaic(dataset,param,out_file,max_value = None, min_value = None):
    # HOW ARE WE PLOTTING:
    # We plot using matplotlib (not xarray direct plotting) on a cartopy axis
    # Have to do some adjustments to matplotlib because of cartopy.
    # Why cartopy, and not basemap?:   https://github.com/SciTools/cartopy/issues/920
    # But we might face the need of a projection not yet in cartopy......
    proj = ccrs.PlateCarree()
    kwargs = {}
    kwargs['colorbar_w'] = 6
    kwargs['show_colorbar'] = True
    kwargs['grid_label_size'] = grid_label_size_mosaic
    kwargs['colorbar_label_size'] = colorbar_label_size_mosaic
    kwargs['colorbar_title_size'] = colorbar_title_size_mosaic
    kwargs['coastline_width'] = coastline_width_mosaic
    
    f, ax = plt.subplots(1, 3, subplot_kw=dict(projection=proj),figsize=(14,7),dpi = 180)
    c = 0
    for agg in mosaic_vdims:
        kwargs['colormap'] = vars_colormap.get('counts')  if agg == 'counts' else vars_colormap.get(param)
        kwargs['colorbar_title'] = var_properties['units'].get('counts') if agg == 'counts' else agg + " (" + var_properties['units'].get(param) + ")"
        kwargs['colorbar_orien'] = 'h'
        if agg == 'counts':
            kwargs['min_value'] = 1; kwargs['max_value'] = dataset['counts'].max()
            z = dataset[agg].where(dataset[agg]> 0).values
            kwargs['normalization'] = LogNorm(vmin=kwargs['min_value'], vmax=kwargs['max_value'])
        else:
            kwargs['min_value'] = dataset[scalable_vdims].min().to_array().min() if min_value is None else min_value
            kwargs['max_value'] = dataset[scalable_vdims].max().to_array().max() if max_value is None else max_value
            kwargs['normalization'] = mpl.colors.Normalize(vmin=kwargs['min_value'], vmax=kwargs['max_value'])
            z = dataset[agg].values
        lons = dataset[agg]['longitude']
        lats = dataset[agg]['latitude']
        map_on_subplot(f,ax[c],z,lons,lats,**kwargs)
        c += 1

    wspace = 0.08# if qc_mode else 0.05
    dpi = 400 #if qc_mode else 300
    plt.subplots_adjust(wspace=wspace,hspace=0.05)#  Force small separation (default is .2, to keep in mind "transparent" colorbar between subplots....THIS WILL DEPEND ON THE FIGURE WIDTH
    plt.savefig(out_file,bbox_inches='tight',dpi = dpi)# 'tight' here, not in plt.tight_layout: here it realizes the new size because of add_axes, but not in plt.tight_layout..
    plt.close()
           
def read_dataset(file,param):
    if param != 'header':
        param_offset = var_properties['offset'].get(param)
        param_scale = var_properties['scale'].get(param)
        dataset = xr.open_dataset(file,autoclose=True)
        for vdim in scalable_vdims:
            dataset[vdim] = param_offset + param_scale*dataset[vdim]
    else:
        dataset = xr.open_dataset(file,autoclose=True)
        
    return dataset
            
            
def main():   
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    try:
        data_path = sys.argv[1]
        release = sys.argv[2]
        update = sys.argv[3]
        source = sys.argv[4]
        level = sys.argv[5]
        sid_dck = sys.argv[6]
        mode = sys.argv[7]
    except Exception as e:
        logging.error(e, exc_info=True)
        return
    
    
    mode_dataset_dict = {'qcr0-qc0-um':'qcr0-qc0',
                         'all':'',
                         'qcr0-qc0':'qcr0-qc0',
                         'qcr0':'qcr0'}
    
    mode_ext_map = {'qcr0-qc0-um':'qcr0-qc0-um-map.png',
                         'all':'all-map.png',
                         'qcr0-qc0':'qcr0-qc0-map.png',
                         'qcr0':'qcr0-map.png'}
    
    mode_ext_mosaic = {'qcr0-qc0-um':'qcr0-qc0-um-mosaic.png',
                         'all':'all-mosaic.png',
                         'qcr0-qc0':'qcr0-qc0-mosaic.png',
                         'qcr0':'qcr0-mosaic.png'}
    
    mode_dataset_hdr_dict = {'qcr0-qc0-um':'qcr0',
                         'all':'',
                         'qcr0-qc0':'qcr0',
                         'qcr0':'qcr0'}
    
    mode_ext_hdr_map = {'qcr0-qc0-um':'qcr0-um-map.png',
                         'all':'all-map.png',
                         'qcr0-qc0':'qcr0-map.png',
                         'qcr0':'qcr0-map.png'}
    
    mode_ext_hdr_mosaic = {'qcr0-qc0-um':'qcr0-um-mosaic.png',
                         'all':'all-mosaic.png',
                         'qcr0-qc0':'qcr0-mosaic.png',
                         'qcr0':'qcr0-mosaic.png'}
    if mode == 'qcr0-qc0-um':
        for param in vars_colormap.keys():
            if param != 'counts':
                vars_colormap[param].set_over('Pink')
                vars_colormap[param].set_under('DarkMagenta')
    
    params = ['header','at','sst','slp','wbt','dpt','wd','ws']
    reports_path = os.path.join(data_path,release,source,level,'reports',sid_dck)

    ext = mode_dataset_dict.get(mode)
    out_ext_map = mode_ext_map.get(mode)
    out_ext_mosaic = mode_ext_mosaic.get(mode)
    for param in params:
        ext = mode_dataset_hdr_dict.get(mode) if param == 'header' else mode_dataset_dict.get(mode)
        out_ext_map = mode_ext_hdr_map.get(mode) if param == 'header' else mode_ext_map.get(mode)
        out_ext_mosaic = mode_ext_hdr_mosaic.get(mode) if param == 'header' else mode_ext_mosaic.get(mode)
        logging.info('Mapping {}'.format(param))
        prefix = '-'.join(['observations',param]) if param != 'header' else 'header'
        pattern = os.path.join(reports_path,'-'.join(filter(bool,[prefix,release,update,ext])) + '.nc')
        
        logging.info('Searching pattern {}'.format(pattern))
        nc_file = glob.glob(pattern)
    
        if len(nc_file) == 0:
            logging.warning('Map not found')
            logging.warning('Empty map figure will not be produced')
            continue
        else:
            logging.info('Loading nc file {}'.format(nc_file))
            dataset = read_dataset(nc_file[0],param)
            # Have a look at the file, maybe there's nothing there!
            non_nans = np.asscalar(dataset['counts'].max().values)
            if non_nans == 0:
                logging.warning('No data in nc file')
                logging.warning('Empty map figure will not be produced')
                continue    

        if param != 'header':
            max_value = var_properties['saturation'].get(param)[1] 
            min_value = var_properties['saturation'].get(param)[0]
            
            for agg in vdims:
                logging.info('Mapping {}'.format(agg))
                out_file =os.path.join(reports_path,'-'.join(filter(bool,[prefix,release,update,agg,out_ext_map])))
                if mode == 'qcr0-qc0-um':
                    map_individual(dataset,agg,param,out_file,max_value = max_value,min_value = min_value)
                else:
                    map_individual(dataset,agg,param,out_file)

            logging.info('Mapping mosaic') 
            out_file =os.path.join(reports_path,'-'.join(filter(bool,[prefix,release,update,out_ext_mosaic])))
            if mode == 'qcr0-qc0-um':
                map_mosaic(dataset,param,out_file,max_value = max_value,min_value = min_value)
            else:
                map_mosaic(dataset,param,out_file)
                
        else:
            
            out_file = os.path.join(reports_path,'-'.join(filter(bool,[prefix,release,update,out_ext_map])))
            map_individual(dataset,'counts',param,out_file)    
    



if __name__ == '__main__':
    main()