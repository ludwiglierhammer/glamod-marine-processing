#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 09:24:24 2020

@author: iregon
"""
import os
import sys
sys.path.append('/Users/iregon/dessaps')
import json
import pandas as pd

import mdf_reader


data_model = 'imma1'
deck_table = 'ICOADS.C1.DCK'
source_table = 'ICOADS.C1.SID'

level2_config_path = '/Users/iregon/C3S/Release_092019/UserManual/L2_config.json' 
level2_path = os.path.dirname(level2_config_path)

table_lib = mdf_reader.code_tables.table_lib

# Open list with final selection of source-decks in release and do some cleaning
with open(level2_config_path,'r') as fileObj:
    level2_config = json.load(fileObj)
    
level2_config.pop('params_exclude',None)


# Open source and deck descriptions from imma1 code tables
decks = mdf_reader.code_tables.read_table(os.path.join(table_lib,data_model,'code_tables',deck_table + '.json'))
sources_trimmed = mdf_reader.code_tables.read_table(os.path.join(table_lib,data_model,'code_tables',source_table + '.json'))
# Reformat sources to be 0 padded
sources = sources_trimmed.copy()
for k,v in sources_trimmed.items():
    if len(k) < 3:
        sources.update({str(int(k)).zfill(3):v})
        sources.pop(k,None)
      
# Drop excluded SID-DECK             
for sd in list(level2_config.keys()):
    if level2_config.get(sd).get('exclude'):
        print('SID-DCK excluded: {}'.format(sd))
        level2_config.pop(sd,None)

# Get the sources and decks with the imma1 code_tables description
level2_sources_list =  list(sorted(set([ x[0:3] for x in level2_config.keys() ]))) 
level2_decks_list =  list(sorted(set([ x[4:] for x in level2_config.keys() ]))) 
level2_sources = { x:sources.get(x) for x in level2_sources_list }
level2_decks = { x:decks.get(x) for x in level2_decks_list }
# Save to simplt csv in L2 config directory
pd.DataFrame.from_dict(level2_decks,orient='index').to_csv(os.path.join(level2_path,'L2_decks.csv'),header=['description'],index_label='Deck IDs')
pd.DataFrame.from_dict(level2_sources,orient='index').to_csv(os.path.join(level2_path,'L2_sources.csv'),header=['description'],index_label='Source IDs')
# See how decks are distributed in sources
deck_sources = dict()
for x in level2_decks:
    ds = []
    for y in level2_sources:
        if y+'-'+x in level2_config:
            ds.append(y)
    deck_sources[x] = ','.join(ds)
    
# See how sources are distributed in decks
source_decks = dict()
for x in level2_sources:
    ds = []
    for y in level2_decks:
        if x+'-'+y in level2_config:
            ds.append(y)
    source_decks[x] = ','.join(ds)
    
pd.DataFrame.from_dict(deck_sources,orient='index').to_csv(os.path.join(level2_path,'L2_deck_sources.csv'),index_label='Deck IDs')
pd.DataFrame.from_dict(source_decks,orient='index').to_csv(os.path.join(level2_path,'L2_source_decks.csv'),index_label='Source IDs')