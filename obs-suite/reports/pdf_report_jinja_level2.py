# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import sys
import os
import glob
import json
import jinja2
from weasyprint import HTML,CSS

try:
    data_path = sys.argv[1]
    release = sys.argv[2]
    update = sys.argv[3]
    source = sys.argv[4]
    sid_dck = sys.argv[5]
    y_init = sys.argv[6]
    y_end = sys.argv[7] 
    level2_list = sys.argv[8]
except Exception as e:
    print("Error processing line argument input to script: ", e)
    exit(1)

#https://stackoverflow.com/questions/45760789/flexbox-centering-within-paper-css-a4-page
FFS = '-'
tables_path = os.path.join(data_path,release,source,'level2',sid_dck)
reports_path = os.path.join(data_path,release,source,'level2','reports',sid_dck)
io_path = reports_path
ts_path = os.path.join(data_path,release,source,'level1e','reports',sid_dck)
maps_path = ts_path
script_path = os.path.dirname(os.path.realpath(__file__))
# PARAMS ----------------------------------------------------------------------

with open(os.path.join(script_path,'sid_properties.json'),'r') as f:
    properties_sid = json.load(f)

with open(os.path.join(script_path,'deck_properties.json'),'r') as f:
    properties_dck = json.load(f)
    
with open(os.path.join(script_path,'var_properties.json'),'r') as f:
    properties_var = json.load(f)
    
params_cdm = ['at','sst','dpt','wbt','slp','wd','ws']

with open(level2_list,'r') as fileObj:
    include_list = json.load(fileObj)

exclude_sid_dck = include_list.get(sid_dck,{}).get('exclude')
if exclude_sid_dck == False:
    print('Include')
else:
    print('Excluded or not included in list')
    sys.exit(0)
    
exclude_param_global_list = include_list.get('params_exclude')
exclude_param_sid_dck_list = include_list.get(sid_dck,{}).get('params_exclude')   
exclude_param_list = list(set(exclude_param_global_list + exclude_param_sid_dck_list))
#=============================== to print....==================================

# Figures and captions general sections =======================================

figures_best = {}
figures_best['C3S_tables'] = os.path.join(io_path,'-'.join(['no_reports',release,update,'qcr0-qc0-ts.png']))
figures_best['C3S_map'] = os.path.join(maps_path,"-".join(['header',release,update,'qcr0-um-map.png']))


captions_best = {}
captions_best['C3S_tables'] = 'Shaded area: number of reports with passed report_quality flag. Series: number observed parameter reports with passed quality_flag flag.'
captions_best['C3S_map'] = 'Spatial distibution of reports. Reports included are those with passed report_quality flag.'

figures_all = {}
figures_all['C3S_tables'] = os.path.join(io_path,'-'.join(['no_reports',release,update,'all-ts.png']))
figures_all['C3S_map'] = os.path.join(maps_path,"-".join(['header',release,update,'all-map.png']))
figures_all['DUP_status'] = os.path.join(io_path,'-'.join(['duplicate_status',release,update,'ts.png'])) 
figures_all['QC_status'] = os.path.join(io_path,'-'.join(['report_quality',release,update,'ts.png']))
figures_all['IO_flow'] = os.path.join(io_path,'-'.join(['io_history',release,update,'ts.png']))

captions_all = {}
captions_all['C3S_tables'] = 'Shaded area: total number of reports included in release (all report_quality flags). Series: number reports from the observed parameter (all quality_flag flags).'
captions_all['C3S_map'] = 'Spatial distibution of reports. Reports of all qualities are included.'
captions_all['DUP_status'] = 'Duplicate status of reports included in release. Series, left axis: number of reports; shaded areas, right axis: stacked percent. Duplicate status are: best duplicate (best), unique report (unique), duplicate (dup), worst duplicate (worst), duplicate status not checked (unchecked)' 
captions_all['QC_status'] = 'Report quality status for reports included in release. Series, left axis: number of reports; shaded areas, right axis: stacked percent. Quality status are: passed (pass), location check failed (loc-fail), quality control of all measured parameters failed while location check passed (param-failed), quality not checked (unchecked)'
captions_all['IO_flow'] = 'Series, left axis: input/output main flow of reports from source data (ICOADS) to dataset included in release. Shaded areas, right axis: percent of invalid data with respect to the initially selected reports (PT selection). Invalid status are: invalid data model (md-invalid), invalid datetime (dt-invalid) and invalid station ID (id-invalid)'


sid = sid_dck.split("-")[0]
deck = sid_dck.split("-")[1]
# Get common titles and figures
sid_name = properties_sid.get(str(sid),str(sid) + ' name: not available')
dck_name = properties_dck.get(str(deck),str(sid) + ' name: not available')
period = ' to '.join([str(y_init),str(y_end)]) 

# Get observed param titles, figures and captions: check if the figures are 
# there, otherwise set caption to empty
# We want the no figure availability to show, but not the correspoding caption

param_items_best = {}
param_items_all = {}
params = [ x for x in params_cdm if 'observations-' + x not in exclude_param_list ]
for param in params:
    # Check for param data in that level2: sid-dck may not have that param
    param_files = glob.glob(os.path.join(tables_path,FFS.join(['observations',param,'*',release,update + '.psv'])))
    if len(param_files) == 0:
        continue
    param_items_best[param]= {}
    param_items_best[param]['long_name'] = properties_var['long_name_upper'].get(param)
    param_items_best[param]['ts'] = os.path.join(ts_path,"-".join(['observations',param,release,update,'qcr0-qc0-um-ts.png']))
    param_items_best[param]['map'] = os.path.join(maps_path,"-".join(['observations',param,release,update,'qcr0-qc0-um-mosaic.png']))
    param_items_all[param]= {}
    param_items_all[param]['long_name'] = properties_var['long_name_upper'].get(param)
    param_items_all[param]['ts'] = os.path.join(ts_path,"-".join(['observations',param,release,update,'all-ts.png']))
    param_items_all[param]['map'] = os.path.join(maps_path,"-".join(['observations',param,release,update,'all-mosaic.png']))
    if not os.path.isfile(param_items_best[param]['ts']):
        param_items_best[param]['caption'] = ''
    else:
        param_items_best[param]['caption'] = 'TOP. Series, left axis: latitudinal band aggregations of {0}: minimum and maximum value (min/max) and mean (mean). The asterisks indicate where values fall outside of the plotting area; Shaded area, right axis: number of reports. BOTTOM. '\
     'Spatial distribution on a 1x1 grid of number of reports (left), minimum value (center) and maximum value (right). '.format(properties_var['long_name_lower'].get(param)) + 'Data values and counts extracted from the best data quality data subset only (report_quality and parameter quality_flag passed).'
    if not os.path.isfile(param_items_all[param]['ts']):
        param_items_all[param]['caption'] = ''
    else:
        param_items_all[param]['caption'] = 'TOP: Series, left axis: latitudinal band aggregations of {0}: minimum and maximum value (min/max) and mean (mean); Shaded areas, right axis: stacked number of reports with different parameter quality status. Quality status are: report and parameter passed (qc passed), parameter qc failed (qc failed), location check failed (qcr failed), quality not checked (qcr unchecked) . BOTTOM: '\
     'Spatial distribution on a 1x1 grid of number of reports (left), minimum value (center) and maximum value (right). '.format(properties_var['long_name_lower'].get(param)) + 'Data values and counts extracted from all the available data from the source. Axis represent the full extent of the data available.'


TEMPLATE_FILE = 'pdf_report_jinja_level2.html'
stylesheet = os.path.join(script_path,'pdf_report_jinja_level2.css')
templateLoader = jinja2.FileSystemLoader(searchpath=script_path)
templateEnv = jinja2.Environment(loader=templateLoader)
template = templateEnv.get_template(TEMPLATE_FILE)

HTMLText = template.render(sid_dck=sid_dck,release = release, update = update,
            sid_name = sid_name, dck_name = dck_name, period = period,
            figures_best = figures_best,captions_best = captions_best,
            figures_all = figures_all,captions_all = captions_all,
            param_items_best = param_items_best,
            param_items_all = param_items_all)


pdf_file = os.path.join(reports_path,'-'.join([sid_dck,release,update,'report.pdf']))

HTML(string=HTMLText,base_url=__file__).write_pdf(pdf_file,stylesheets=[CSS(stylesheet)], presentational_hints=True)

#with open('/Users/iregon/dessaps/data/112-926/' + '1.html', 'w') as html_file:
#    html_file.write(HTMLText)
#    html_file.close()



