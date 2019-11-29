#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 15:25:03 2019

Creates gridded aggregations of all the available CDM tables per table per sid-dck.

Aggregations are:
    header table: counts
    observation tables: counts,max,min,mean

Data is first filtered according to inargs qcr and qc


Inargs:
------
data_path: data release parent path (i.e./gws/nopw/c3s311_lot2/data/marine)
sid_dck: source-deck partition (sss-ddd)
release: release identifier
update: release update identifier
source: source dataset identifier
level: data processing level (level1e|level2)
table: CDM table to process (header or observations-[sst|slp|at|wd|ws|wbt|dpt])
qcr: all or any single or comma separated combination of CDM table quality_flag keys
qc: all or any single or comma separated combination of CDM table quality_flag keys
scratch_dir: directory to save (and remove) intermediate files to

@author: iregon
"""
import sys
import os
import logging
import cdm

def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    try:
        data_path = sys.argv[1]
        release = sys.argv[2]
        update = sys.argv[3]
        source = sys.argv[4]
        level = sys.argv[5]
        sid_dck = sys.argv[6]
        table = sys.argv[7]
        qcr = sys.argv[8]
        qc = sys.argv[9]
        scratch_dir = sys.argv[10] 
    except Exception as e:
        logging.error(e, exc_info=True)
        return

    logging.info(data_path)
    release_path = os.path.join(data_path,release)
    release_source_path = os.path.join(release_path,source)
    level_data_path = os.path.join(release_source_path,level,sid_dck)
    reports_path = os.path.join(release_source_path,level,'reports',sid_dck)

    logging.info('QC settings:{0},{1}'.format(qcr,qc))
    qcr = None if qcr == 'all' else [ int(x) for x in qcr.split(',') ]
    qc = None if qc == 'all' else [ int(x) for x in qc.split(',') ]
    if qc:
        logging.info('QC settings:{}'.format(','.join(filter(bool,[ str(x) for x in qcr]))))
    
    if not os.path.isdir(level_data_path):
        logging.error('Path to {0} data {1} not found'.format(level,level_data_path))
        return
    
    if not os.path.isdir(reports_path):
        logging.error('Path to {0} reports {1} not found'.format(level,reports_path))
        return

    cdm_id = '-'.join(filter(bool,[release,update]))
    cdm.gridded_stats.global_from_monthly_cdm(level_data_path,cdm_id = cdm_id, nc_dir = reports_path, qc = qc,qc_report = qcr, scratch_dir = scratch_dir, tables = [table])

if __name__ == '__main__':
    main()
