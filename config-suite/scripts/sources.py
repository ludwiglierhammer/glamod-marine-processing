import pandas as pd
from pathlib import Path
from imma_noc import *
import os
import sys
import argparse
import datetime as dt
from dateutil.relativedelta import relativedelta

imiss = -999999
fmiss = -999999.0
cmiss = 'MSNG'

pd.options.display.max_columns = 100


class smart_dict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)

    def __missing__(self, key):
        # key = ''
        if key == '':
            val = cmiss
        else:
            val = key
        return val


def main(argv):
    parser = argparse.ArgumentParser(description='Summarise stations for given month / year based on CDM file')

    parser.add_argument("-schema", dest="schema", required=True, \
                        help="JSON file containing schema for IMMA format", default=None)
    parser.add_argument("-code_tables", dest="code_tables", required=True, \
                        help="Directory containing code tables for IMMA format", default=None)
    parser.add_argument("-index", dest="index", required=True, \
                        default=None, type=int, help="Index of month to process, month 1 = Jan 1946")
    parser.add_argument("-imma_source", dest="source", required=True, default=None, \
                        help="Directory containing original IMMA data")
    parser.add_argument("-destination", dest="destination", required=True, default=None, \
                        help="Target directory to write data to")
    args = parser.parse_args()


    # load source template
    template_file = 'source_template.csv'
    source_template = pd.read_csv( template_file , sep ='|', dtype='object', low_memory = False )
    source_template.set_index( 'source_key', inplace = True)
    
    # identify which sources / deck we are processing
    # elements to fill in
    # 1) source file
    # 2) source file cksum
    # 3) bbox min latitude
    # 4) bbox max latitude
    # 5) bbox min longitude
    # 6) bbox max longitude
    # 7) min date
    # 8) max date

    idx = args.index - 1
    mm = pd.np.arange( 732 )
    dates = list( dt.datetime( 1950, 1 , 1) + relativedelta( months = m ) for m in mm )
    d = dates[idx]

    iyear = d.year
    imonth = d.month
    # now load IMMA file for month and merge certain fields with datain to determine observed variables
    # initialise IMMA reader
    icoads_dir = args.source
    filename = icoads_dir + 'IMMA1_R3.0.0T_{:04d}-{:02d}'.format(iyear, imonth)
    input_schema = args.schema
    code_tables = args.code_tables
    imma_obj = imma(schema=input_schema, code_tables=code_tables, sections=['core', 'ATTM1', 'ATTM98'])
    imma_obj.loadImma(filename, sections=['core', ' 1', '98'], verbose=True, block_size=None)

    print(' Data read, md5: {}'.format(imma_obj.cksum) )

    print( imma_obj.data )
    
    datain = imma_obj.data[ ['core.lon','core.lat','attm1.dck','attm1.sid'] ].copy()
    print(datain)
    #datain['source_id'] = datain.apply( lambda x: 'ICOADS-3-0-0T-{:03d}-{:03d}-{:04d}-{:02d}'.format( int( x['attm1.sid']) , int( x['attm1.dck'] ), iyear, imonth), axis = 1 )
    datain['source_id'] = datain.apply( lambda x: '{:03d}-{:03d}'.format( int( x['attm1.sid']) , int( x['attm1.dck'] )), axis = 1 )
    sources_grouped = datain.groupby(['source_id'])
    
    summary = sources_grouped.agg(
                                   bbox_min_lon=pd.NamedAgg(column='core.lon', aggfunc='min'),
                                   bbox_max_lon=pd.NamedAgg(column='core.lon', aggfunc='max'),
                                   bbox_min_lat=pd.NamedAgg(column='core.lat', aggfunc='min'),
                                   bbox_max_lat=pd.NamedAgg(column='core.lat', aggfunc='max') )

    # merge with template to add fixed source / deck information
    summary = pd.merge( summary, source_template, how = "left", left_index = True, right_index = True )

    # reset index
    summary.reset_index(inplace = True)
    summary['source_id'] = summary['source_id'].apply( lambda x: 'ICOADS-3-0-0T-{}-{:04d}-{:02d}'.format(x, iyear, imonth) )

    # source_id
    summary = summary.assign( product_id = 'IC30' )
    # product name
    summary = summary.assign( product_code = 'ICOADS' )
    summary = summary.assign( product_version = 'Release 3.0.0 Total')
    summary = summary.assign( product_level = 'NULL' )
    summary = summary.assign( product_uri = 'https://icoads.noaa.gov/')
    # description
    # product_references
    # product_citation
    summary = summary.assign( product_status = 'NULL')
    summary = summary.assign( source_format = 1 )
    summary = summary.assign( source_format_version = 1 )
    summary = summary.assign( source_file = 'IMMA1_R3.0.0T_{:04d}-{:02d}'.format(iyear, imonth) )
    summary = summary.assign( source_file_cksum = imma_obj.cksum )
    summary = summary.assign( data_centre = 'NULL' )
    summary = summary.assign( data_centre_url = 'https://rda.ucar.edu/datasets/ds548.0/' )
    summary = summary.assign( data_policy_licence = 0 )
    summary = summary.assign( contact = '{1}')
    summary = summary.assign( contact_role = '{5}')
    summary = summary.assign( history = 'NULL' )
    summary = summary.assign( comments = 'NULL' )
    summary = summary.assign( timestamp = 'NULL')
    summary = summary.assign( maintenance_and_update_frequency = 0 )
    summary = summary.assign( optional_data = 0 )
    # bbox_min_lon
    # bbox_max_lon
    # bbox_min_lat
    # bbox_max_lat
    summary = summary.assign( metadata_contact = '{1}')
    summary = summary.assign( metadata_contact_role = '{5}')
    

    outfile = '{:04d}-{:02d}.csv'.format( iyear, imonth )


    field_order = ['source_id','product_id','product_name','product_code','product_version','product_level','product_uri',
                    'description','product_references','product_citation','product_status','source_format','source_format_version',
                    'source_file','source_file_cksum','data_centre','data_centre_url','data_policy_licence','contact','contact_role',
                    'history','comments','timestamp','maintenance_and_update_frequency','optional_data','bbox_min_lon','bbox_max_lon',
                    'bbox_min_lat','bbox_max_lat','metadata_contact','metadata_contact_role']

    summary[field_order].to_csv(args.destination + './' + outfile, index=False, sep='|', na_rep='NULL', doublequote=False, escapechar='\\')


if __name__ == '__main__':
    main(sys.argv[1:])

