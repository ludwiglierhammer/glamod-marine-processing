#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 10:18:42 2019

Aggregates info from monthly nc maps in /level1e/quicklooks/ to generate time series in latitudinal bands  

@author: iregon
"""

import xarray as xr
import glob
import datetime
import pandas as pd
import os
import json
import numpy as np
import logging
import sys
import itertools

import matplotlib.pyplot as plt
#plt.switch_backend('agg')


script_path = os.path.dirname(os.path.realpath(__file__))

# PARAMS ----------------------------------------------------------------------

with open(os.path.join(script_path,'var_properties.json'),'r') as f:
    var_properties = json.load(f)
    
params = ['at','sst','slp','ws','wd','dpt','wbt']
vdims = ['counts','max','min','mean']
scalable_vdims = ['max','min','mean']
kdims = ['latitude', 'longitude']
latitude_bins = [-90,-60,-30,30,60,90]
bin_tags = [ '/'.join([str(latitude_bins[i]),str(latitude_bins[i+1])]) for i in range(0,len(latitude_bins)-1) ]

# Some plotting options
font_size_legend = 11
axis_label_size = 11
tick_label_size = 9
title_label_size = 14
markersize = 3
figsize=(12, 14)
    
plt.rc('legend',**{'fontsize':font_size_legend})        # controls default text sizes
plt.rc('axes', titlesize=axis_label_size)     # fontsize of the axes title
plt.rc('axes', labelsize=axis_label_size)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('ytick', labelsize=tick_label_size)    # fontsize of the tick labels
plt.rc('figure', titlesize=title_label_size)  # fontsize of the figure title
# END PARAMS ------------------------------------------------------------------



# FUNCTIONS  ------------------------------------------------------------------

def flip(items, ncol):
    return itertools.chain(*[items[i::ncol] for i in range(ncol)])

def read_dataset(files):
    dataset = xr.open_mfdataset(files,autoclose=True,concat_dim = 'time')
    #time_stamps = [ datetime.datetime(int(os.path.basename(x).split('-')[2]),int(os.path.basename(x).split('-')[3]),1) for x in files]
    #dataset = dataset.assign_coords(time=time_stamps)  
    return dataset
    

def create_lat_bands(dataset,agg=None):
    latitude_band_aggs = {}
    if agg == 'params':
        latitude_band_aggs = {}
        aggregation = 'max'
        latitude_band_aggs[aggregation] = dataset[aggregation].groupby_bins('latitude', latitude_bins).max(kdims,skipna=True)
        aggregation = 'min'
        latitude_band_aggs[aggregation] = dataset[aggregation].groupby_bins('latitude', latitude_bins).min(kdims,skipna=True)
        aggregation = 'mean'
        latitude_band_aggs[aggregation] = dataset[aggregation].groupby_bins('latitude', latitude_bins).mean(kdims,skipna=True) 
    elif agg == 'counts':
        latitude_band_aggs = {}
        aggregation = agg
        latitude_band_aggs[aggregation] = dataset[aggregation].groupby_bins('latitude', latitude_bins).sum(kdims,skipna=True)    
    
    return latitude_band_aggs

def plot_lat_bands(mode,param,param_latitude_band_aggs,counts_latitude_band,max_value,min_value,fig_path):
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    start = param_latitude_band_aggs['time'].min().values#isel(time=0).values
    end = param_latitude_band_aggs['time'].max().values#isel(time=-1).values
    index = pd.date_range(start=start,end=end,freq='MS') 
    
    start = counts_latitude_band['time'].isel(time=0).values
    end = counts_latitude_band['time'].isel(time=-1).values
    counts_index = pd.date_range(start=start,end=end,freq='MS')
    
    param_units = var_properties['units'].get(param)
    param_offset = var_properties['offset'].get(param)
    param_scale = var_properties['scale'].get(param)
    
    bin_tags = [ '/'.join([str(x.left),str(x.right)]) for x in counts_latitude_band['latitude_bins'].values ]
    
    xmin = counts_index[0] - datetime.timedelta(days=15)
    xmax = counts_index[-1] + datetime.timedelta(days=15)
    bbox_props = dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9)


    ax2 = ['']*len(bin_tags)
    fig, ax = plt.subplots(nrows=len(bin_tags), ncols=1, figsize=figsize, dpi=150)
    ax_count = 0
    # Get ready for no data plotted....mainly obss params, rahter than counts
    lines = None
    lines2 = None
    labels = None
    labels2 = None
    for i in range(len(bin_tags)-1,-1,-1):
        bin_tag = bin_tags[i]
        param_lat_df = pd.DataFrame(index = index,columns = vdims)
        

        for aggregation in scalable_vdims:
            param_lat_df[aggregation].loc[param_latitude_band_aggs[aggregation]['time'].values] = param_latitude_band_aggs[aggregation].isel(latitude_bins=i).values 
            
        param_lat_df = param_offset + param_scale*param_lat_df
        
        counts_lat_df = pd.DataFrame(index = counts_index,columns = ['counts all','counts optimal'])
        for status in ['counts all','counts optimal']:
            counts_lat_df[status].loc[counts_latitude_band[status]['time'].values] = counts_latitude_band[status].isel(latitude_bins=i).values   
        
        # Create a new series for outliers (data out of plot bounds)
        # The max_value - 1 and min_value + 1 so that they are clear in the plot
        if mode == 'optimal':
            param_lat_df['max-sat'] = param_lat_df['max'].loc[param_lat_df['max'] > max_value]
            param_lat_df.loc[param_lat_df['max-sat'].notna(),'max-sat'] = max_value - 1
            param_lat_df['min-sat'] = param_lat_df['min'].loc[param_lat_df['min'] < min_value]
            param_lat_df.loc[param_lat_df['min-sat'].notna(),'min-sat'] = min_value + 1
        
        # Do not plot if no data
        if not np.isnan(param_lat_df['max'].max(skipna=True)):
        #if (counts_lat_df[mode_dataset].sum()) > 0:    
            ax[ax_count].plot(param_lat_df.index,param_lat_df['max'],marker = '.',linestyle=' ',color='OrangeRed',label='_nolegend_',markersize = markersize,zorder=7)
            ax[ax_count].plot(param_lat_df.index,param_lat_df['min'],marker = '.',linestyle=' ',color='OrangeRed',label='min/max',markersize = markersize,zorder=7)
            if mode == 'optimal':
                ax[ax_count].plot(param_lat_df.index,param_lat_df['max-sat'],marker = '*',linestyle=' ',color='Red',label='_nolegend_',markersize = markersize + 2,zorder=7)
                ax[ax_count].plot(param_lat_df.index,param_lat_df['min-sat'],marker = '*',linestyle=' ',color='Red',label='off-plot',markersize = markersize + 2,zorder=7)
            ax[ax_count].plot(param_lat_df.index,param_lat_df['mean'],linestyle ='-',color='black',label='mean',zorder=6)
            ax[ax_count].set_ylabel(param_units, color='k')
            ax[ax_count].grid(linestyle=':',which='major')
            ax[ax_count].set_ylim(min_value,max_value)
            ax[ax_count].set_xlim([xmin, xmax])
            ax[ax_count].text(0.99, 0.9, bin_tag , horizontalalignment='right',verticalalignment='center', transform=ax[ax_count].transAxes)
            lines, labels = ax[ax_count].get_legend_handles_labels()
        else:
            ax[ax_count].set_xlim([xmin, xmax])
            ax[ax_count].set_ylim(min_value,max_value)
            xmid = xmin + (xmax-xmin)//2
            ax[ax_count].text(xmid, min_value + (max_value-min_value)/2, "No data", ha="center", va="center", size=20,bbox=bbox_props)
            ax[ax_count].text(0.99, 0.9, bin_tag , horizontalalignment='right',verticalalignment='center', transform=ax[ax_count].transAxes) 
        
        if mode == 'optimal':
            ax2[ax_count] = ax[ax_count].twinx()
            ax2[ax_count].fill_between(counts_lat_df.index,0,counts_lat_df['counts optimal'].astype('float'), facecolor='Gray',alpha=0.25,interpolate=False,label='no.reports',zorder=1)
            ax2[ax_count].set_ylabel('counts', color='k')
        else:
            ax2[ax_count] = ax[ax_count].twinx()
            ax2[ax_count].fill_between(counts_lat_df.index,0,counts_lat_df['counts optimal'].astype('float'), facecolor='Gray',alpha=0.25,interpolate=False,label='qc passed',zorder=1)
            ax2[ax_count].fill_between(counts_lat_df.index,counts_lat_df['counts optimal'].astype('float'),counts_lat_df['counts all'].astype('float'), facecolor='OrangeRed',alpha=0.25,interpolate=False,label='qc failed',zorder=2)
            ax2[ax_count].plot(counts_lat_df.index,counts_lat_df['counts all'],linestyle=':',color='Grey',marker = '.',label='all reports',markersize = markersize,linewidth=1,zorder=4)
            ax2[ax_count].set_ylabel('counts', color='k')
         # Now send the histogram to the back
        ax[ax_count].set_zorder(ax2[ax_count].get_zorder()+1) # put ax in front of ax2
        ax[ax_count].patch.set_visible(False) # hide the 'canvas'
        #ax_y_lim = [ int(min_value - 0.2*(max_value-min_value)),int(max_value +  0.2*(max_value-min_value)) ]
        #ax[ax_count].set_ylim(ax_y_lim)
        lines2, labels2 = ax2[ax_count].get_legend_handles_labels()   
    
        
        ax_count += 1

    ncols_leg = 4
    if lines is not None:      
        ax[len(bin_tags)-1].legend(flip(lines + lines2,ncols_leg),flip(labels + labels2,ncols_leg),loc='center', bbox_to_anchor=(0.5, -0.35),ncol=ncols_leg)
    else:
        ax[len(bin_tags)-1].legend(lines2,labels2,loc='center', bbox_to_anchor=(0.5, -0.35),ncol=5) 
    title_param = " ".join([ x.capitalize() for x in var_properties['long_name_lower'].get(param).split(' ')])
    y_ini = counts_index[0].strftime('%Y')
    y_end = counts_index[-1].strftime('%Y')
    fig.suptitle(title_param + '\n' + " to ".join([str(y_ini),str(y_end)]))
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    logging.info('Saving figure to {}'.format(fig_path))
    plt.savefig(fig_path,bbox_inches='tight',dpi = 300)
    plt.close(fig)

def main():   
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    try:
        data_summaries_path = sys.argv[1]
        release = sys.argv[2]
        dataset = sys.argv[3]
        sid_dck = sys.argv[4] 
        mode = sys.argv[5]
        param = sys.argv[6] # ['at','sst',....]
        out_dir = sys.argv[7]
    except Exception as e:
        logging.error(e, exc_info=True)
        return


#    DIRTY WAY OF DOING THINGS                
    nc_path = os.path.join(data_summaries_path,release,dataset,sid_dck)
   
    logging.info('Data path is {}'.format(nc_path))
    logging.info('Reports path is {}'.format(out_dir))
 
    logging.info('Plotting {}'.format(param))
    all_patterns = os.path.join(nc_path,'-'.join(['observations',param,'????-??-all.nc']))
    optimal_patterns = os.path.join(nc_path,'-'.join(['observations',param,'????-??-optimal.nc']))

    logging.info('Searching pattern {}'.format(all_patterns))
    all_files = glob.glob(all_patterns)
    optimal_files = glob.glob(optimal_patterns)
    
#    DIRTY WAY OF NOT PRODUCING EMPTY TSs    
    if mode == 'all' and len(all_files) == 0:
        logging.warning('No maps found for all report types')
        logging.warning('Empty ts will not be produced')
        sys.exit(0)
    elif mode == 'optimal' and len(optimal_files) == 0:
        logging.warning('No maps found for quality passed records found')
        logging.warning('Empty ts will not be produced')
        sys.exit(0)
    else:
        datasets = {}
        logging.info('Reading nc files (all reports)')
        datasets['all'] = read_dataset(all_files) 
        logging.info('Reading nc files (optimal)')
        datasets['optimal'] = read_dataset(optimal_files)
        
        
#       create count aggregations          
        logging.info('Lat aggregation (all reports)')
        all_latitude_band_counts = create_lat_bands(datasets['all'],agg='counts')['counts'].to_dataset(name='counts all')
        logging.info('Lat aggregation (optimal reports)')
        optimal_latitude_band_counts = create_lat_bands(datasets['optimal'],agg='counts')['counts'].to_dataset(name='counts optimal')
        
        counts_datasets = [all_latitude_band_counts,optimal_latitude_band_counts]
        counts_latitude_band = xr.merge(counts_datasets)
        
        nc_path = os.path.join(out_dir,'-'.join(['observations',param,'ts',mode]) + '.nc')
        fig_path = os.path.join(out_dir,'-'.join(['observations',param,release,'ts',mode]) + '.png')
        
        logging.info('Plotting mode {}'.format(mode))
        logging.info('With dataset values {}'.format(mode))
        param_latitude_band_dict = create_lat_bands(datasets[mode],agg='params')
        params_datasets = [param_latitude_band_dict['max'].to_dataset(name='max'),
                                             param_latitude_band_dict['min'].to_dataset(name='min'),
                                             param_latitude_band_dict['mean'].to_dataset(name='mean')]
        param_latitude_band_aggs = xr.merge(params_datasets)
        
        # Set the y-axis max-min values
        total_counts = np.asscalar(counts_latitude_band['counts reports [0] param [0]'].sum(skipna=True).values)
        if mode == 'optimal':
            logging.info('Plotting mode {} with bounded axis'.format(mode))
            max_value = var_properties['saturation'].get(param)[1]
            min_value = var_properties['saturation'].get(param)[0]
        elif total_counts == 0: # we might not be producing nc file if no data, and this case will not happen...
            max_value = var_properties['saturation'].get(param)[1]
            min_value = var_properties['saturation'].get(param)[0] 
        else:    
            max_value = var_properties['offset'].get(param) + \
                    var_properties['scale'].get(param)*np.nanmax(param_latitude_band_dict['max'].values)
            max_value = max_value + max(1,0.05*max_value)# So that extremes are clear in plot
            min_value = var_properties['offset'].get(param) + \
                    var_properties['scale'].get(param)*np.nanmin(param_latitude_band_dict['min'].values)
            min_value = min_value - max(1,0.05*min_value) # So that extremes are clear in plot
            
        plot_lat_bands(mode,param,param_latitude_band_aggs,counts_latitude_band,max_value,min_value,fig_path)
        
        merged = xr.merge([counts_latitude_band,param_latitude_band_aggs])
        # This is because xarray cannot serialize the lat-band interval type...
        merged.coords['latitude_bins'] = [ '/'.join([str(x.left),str(x.right)]) for x in merged.coords['latitude_bins'].values ]
        merged.to_netcdf(nc_path,mode='w')  

if __name__ == '__main__':
    main()
