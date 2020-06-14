#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 20 11:43:22 2018

@author: iregon
"""
import os
import logging
import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import datetime
import xarray as xr
from matplotlib.colors import LogNorm

from figures import var_properties


# PARAMS ----------------------------------------------------------------------
# Set plotting defaults
plt.rc('legend',**{'fontsize':8})        # controls default text sizes
plt.rc('axes', titlesize=8)     # fontsize of the axes title
plt.rc('axes', labelsize=8)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=6)    # fontsize of the tick labels
plt.rc('ytick', labelsize=6)    # fontsize of the tick labels
plt.rc('figure', titlesize=10)  # fontsize of the figure title
figsize=(6,6)
# END PARAMS ------------------------------------------------------------------

def is_season_center(month,season):
    if season == 'DJF':
        return month == 1   
    elif season == 'MAM':
        return month == 4
    elif season == 'JJA':
        return month == 7
    elif season == 'SON':
        return month == 10

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
#    dir_data = sys.argv[1]
#    dir_out = sys.argv[2]
    
    dir_data = '/group_workspaces/jasmin2/glamod_marine/data/user_manual/v4/level2/quicklooks/'
    dir_out = dir_data
    file_in_id = '-no_reports_grid_ts-optimal.nc'
    file_out = 'nreports_hovmoller.png'
    start = datetime.datetime(1851,1,1)
    stop = datetime.datetime(2010,12,31)
    
    tables = ['header','observations-at','observations-sst','observations-slp',
                      'observations-dpt','observations-wd','observations-ws']
    
    for table in tables:
        logging.info('Plotting table {}'.format(table))
        if table == 'header':
            cbar_label = '#reports'   
        else:
            param = table.split('-')[1]
            cbar_label = '#Observations ' + var_properties.var_properties['short_name_upper'][param]
        
        file_pattern = table + file_in_id
        dataset = xr.open_dataset(os.path.join(dir_data,file_pattern))
        
        dataset['3_mon_counts'] = dataset['counts'].rolling(time=3, center=True).sum()
        for season in ['DJF','MAM','JJA','SON']:
            dataset[season] = dataset['3_mon_counts'].sel(time=is_season_center(dataset['time.month'],season)).sum(dim='longitude')
            
        min_counts = 1
        if table == 'header': # Use same scale for all params
            max_counts = dataset['3_mon_counts'].max().data.tolist()
            normalization_f = LogNorm(vmin = min_counts,vmax = max_counts)
        
        f, axes = plt.subplots(nrows=2, ncols=2, figsize=figsize)
        for i, season in enumerate(['DJF','MAM','JJA','SON']):
            c = 0 if i%2 == 0 else 1
            r = int(i/2)
            dataset[season].sel(time=is_season_center(dataset['time.month'],season)).where(dataset[season]>0).plot.pcolormesh(x = 'time', y = 'latitude',vmin=min_counts,
                       vmax=max_counts, cmap='viridis',norm = normalization_f,add_colorbar=True,
                       extend='both',ax=axes[c,r],cbar_kwargs={'label':cbar_label})
            axes[c,r].set_title(season)
        f.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig_path = os.path.join(dir_out,table + '-' + file_out)
        plt.savefig(fig_path,bbox_inches='tight',dpi = 150)
        plt.close(f)
