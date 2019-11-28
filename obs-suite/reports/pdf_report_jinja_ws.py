# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import sys
import os
import json
import jinja2
from weasyprint import HTML,CSS
import pandas as pd

try:
    data_path = sys.argv[1]
    release = sys.argv[2]
    update = sys.argv[3]
    source = sys.argv[4]
    sid_list = sys.argv[5]
except Exception as e:
    print("Error processing line argument input to script: ", e)
    exit(1)

#https://stackoverflow.com/questions/45760789/flexbox-centering-within-paper-css-a4-page

script_path = os.path.dirname(os.path.realpath(__file__))
# PARAMS ----------------------------------------------------------------------

with open(os.path.join(script_path,'sid_properties.json'),'r') as f:
    properties_sid = json.load(f)

with open(os.path.join(script_path,'deck_properties.json'),'r') as f:
    properties_dck = json.load(f)
    
with open(os.path.join(script_path,'var_properties.json'),'r') as f:
    properties_var = json.load(f)
    
params = ['at','sst','dpt','wbt','slp','wd','ws']

sid_ref = '032-927'
#=============================== to print....==================================

# Figures and captions general sections =======================================

list_sid = pd.read_csv(sid_list,usecols=[0],delimiter='\t',names=['sid'],header=None)


reports_path = os.path.join(data_path,release,source,'level1e','reports',sid_ref)
ref = {}
ref['sid'] = sid_ref
ref['histogram'] = os.path.join(reports_path,'-'.join([sid_ref,'observations','ws','histogram']) + '.png')
ref['histogram_log'] = os.path.join(reports_path,'-'.join([sid_ref,'observations','ws','histogram','log']) + '.png')
ref['map'] = os.path.join(reports_path,'-'.join(['observations','ws',release,update,'max-all-map.png']))
ref['map_counts'] = os.path.join(reports_path,'-'.join(['observations','ws',release,update,'counts-all-map.png']))
ref['ts'] = os.path.join(reports_path,'-'.join([sid_ref,'observations','ws','all','ts','global']) + '.png')

print(ref)

sid_params = {}
for sid in list_sid['sid']:
    if sid == sid_ref:
        continue
    reports_path = os.path.join(data_path,release,source,'level1e','reports',sid)
    sid_params[sid] = {}
    sid_params[sid]['ts'] = os.path.join(reports_path,'-'.join([sid,'observations','ws','all','ts','global']) + '.png')
    sid_params[sid]['histogram'] = os.path.join(reports_path,'-'.join([sid,'observations','ws','histogram']) + '.png')
    sid_params[sid]['histogram_log'] = os.path.join(reports_path,'-'.join([sid,'observations','ws','histogram','log']) + '.png')
    sid_params[sid]['map'] = os.path.join(reports_path,'-'.join(['observations','ws',release,update,'max-all-map.png']))
    sid_params[sid]['map_counts'] = os.path.join(reports_path,'-'.join(['observations','ws',release,update,'counts-all-map.png']))

TEMPLATE_FILE = 'pdf_report_jinja_ws.html'
stylesheet = os.path.join(script_path,'pdf_report_jinja_ws.css')
templateLoader = jinja2.FileSystemLoader(searchpath=script_path)
templateEnv = jinja2.Environment(loader=templateLoader)
template = templateEnv.get_template(TEMPLATE_FILE)

HTMLText = template.render(sid_params=sid_params,ref=ref)

reports_path = os.path.join(data_path,release,source,'level1e','reports')
pdf_file = os.path.join(reports_path,'-'.join([release,update,'ws','report.pdf']))

HTML(string=HTMLText,base_url=__file__).write_pdf(pdf_file,stylesheets=[CSS(stylesheet)], presentational_hints=True)

#with open('/Users/iregon/dessaps/data/112-926/' + '1.html', 'w') as html_file:
#    html_file.write(HTMLText)
#    html_file.close()



