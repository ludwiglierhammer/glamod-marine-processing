#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 20 11:43:22 2018

@author: iregon
"""
import os
import sys
import logging
import matplotlib.pyplot as plt
#plt.switch_backend('agg')
import datetime
import itertools
import xarray as xr
from matplotlib.colors import LogNorm
import cartopy.crs as ccrs

from figures import var_properties

logging.getLogger('plt').setLevel(logging.INFO)
logging.getLogger('mpl').setLevel(logging.INFO)

# PARAMS ----------------------------------------------------------------------
# Set plotting defaults
plt.rc('legend',**{'fontsize':12})        # controls default text sizes
plt.rc('axes', titlesize=12)     # fontsize of the axes title
plt.rc('axes', labelsize=12)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=10)    # fontsize of the tick labels
plt.rc('ytick', labelsize=10)    # fontsize of the tick labels
plt.rc('figure', titlesize=14)  # fontsize of the figure title
# END PARAMS ------------------------------------------------------------------

def is_jan(month):
    return month == 1

def is_apr(month):
    return month == 4

def is_jul(month):
    return month == 7

def is_oct(month):
    return month == 10

seasonal_data = temp_data.sel(time=is_amj(temp_data['time.month']))

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    dir_data = sys.argv[1]
    dir_out = sys.argv[2]
    
dir_data = '/Users/iregou/C3S/data'
dir_out = dir_data
file_in_id = '-no_reports_grid_ts-optimal.nc'
file_out = 'params_no_reports_coverage_ts.pdf'
start = datetime.datetime(1851,1,1)
stop = datetime.datetime(2010,12,31)
 
table = 'header'
file_pattern = table + file_in_id

hdr_dataset = xr.open_dataset(os.path.join(dir_data,file_pattern))
hdr_dataset['counts'] = hdr_dataset['counts'].where(hdr_dataset['counts']<1,1) 
hdr_dataset['counts'] = hdr_dataset['counts'].rolling(time=3, center=True).max()
hdr_dataset['DJF'] = hdr_dataset['counts'].sel(time=is_jan(hdr_dataset['time.month'])).sum(dim='time')
hdr_dataset['MAM'] = hdr_dataset['counts'].sel(time=is_apr(hdr_dataset['time.month'])).sum(dim='time')
hdr_dataset['JJA'] = hdr_dataset['counts'].sel(time=is_jul(hdr_dataset['time.month'])).sum(dim='time')
hdr_dataset['SON'] = hdr_dataset['counts'].sel(time=is_oct(hdr_dataset['time.month'])).sum(dim='time')

max_counts = 2010-1851+1
min_counts = 1
normalization_f = LogNorm(vmin = min_counts,vmax = max_counts)

proj = ccrs.PlateCarree()

f, axes = plt.subplots(nrows=2, ncols=2, subplot_kw=dict(projection=proj),figsize=(10,10))

for i, season in enumerate(['DJF','MAM','JJA','SON']):
    c = 0 if i%2 == 0 else 1
    r = int(i/2)
    hdr_dataset[season].where(hdr_dataset[season]>0).plot.pcolormesh(vmin=min_counts,
               vmax=max_counts, cmap='viridis',norm = normalization_f,add_colorbar=True,
               extend='both',transform = ccrs.PlateCarree(),ax=axes[c,r])
f.tight_layout(rect=[0, 0.03, 1, 0.95])