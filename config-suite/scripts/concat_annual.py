import pandas as pd
from pathlib import Path
import sys
import argparse


def main(argv):

    parser = argparse.ArgumentParser(description='Concatenate monthly summaries to annual')
    parser.add_argument("-work", dest="work", required=True, default=None, \
                        help="Directory containing monthly summaries")
    parser.add_argument("-year", dest="year", required=True, default=None, \
                        help="Year to process", type=int)

    args = parser.parse_args()


    work_directory = args.work# '/group_workspaces/jasmin2/glamod_marine/working/config-suite/out/'
    iyear = args.year # 1977

    files = Path(work_directory).glob("**/stations-{:04d}-*.csv".format(iyear))
    datain = None
    for file in files:
        print(str(file))
        tmp = pd.read_csv(file, sep='|', dtype='object')
        tmp['observed_variables'] = tmp['observed_variables'].fillna('')
        tmp['station_name'] = tmp['station_name'].fillna('UNKNOWN STATION')
        tmp['alternative_name'] = tmp['alternative_name'].fillna('NULL')
        # convert dates to dates
        # convert bbox to numeric
        tmp['start_date'] = pd.to_datetime(tmp['start_date'])
        tmp['end_date'] = pd.to_datetime(tmp['end_date'])
        tmp['bbox_min_lon'] = pd.to_numeric(tmp['bbox_min_lon'])
        tmp['bbox_max_lon'] = pd.to_numeric(tmp['bbox_max_lon'])
        tmp['bbox_min_lat'] = pd.to_numeric(tmp['bbox_min_lat'])
        tmp['bbox_max_lat'] = pd.to_numeric(tmp['bbox_max_lat'])
        if datain is None:
            datain = tmp.copy()
        else:
            datain = pd.concat([datain, tmp])
    
    #datain.fillna('NULL',inplace=True)
    
    stations_grouped = datain.groupby(['primary_station_id', 'primary_station_id_scheme', 'station_record_number', 'platform_type'] )

    summary = stations_grouped.agg(
                                    start_date               = pd.NamedAgg(column='start_date',                aggfunc='min'),
                                    end_date                 = pd.NamedAgg(column='end_date',                  aggfunc='max'),
                                    bbox_min_lon             = pd.NamedAgg(column='bbox_min_lon',              aggfunc='min'),
                                    bbox_max_lon             = pd.NamedAgg(column='bbox_max_lon',              aggfunc='max'),
                                    bbox_min_lat             = pd.NamedAgg(column='bbox_min_lat',              aggfunc='min'),
                                    bbox_max_lat             = pd.NamedAgg(column='bbox_max_lat',              aggfunc='max'),
                                    station_name             = pd.NamedAgg(column='station_name',              aggfunc='unique'),
                                    secondary_id             = pd.NamedAgg(column='secondary_id',              aggfunc='unique'),
                                    secondary_id_scheme      = pd.NamedAgg(column='secondary_id_scheme',       aggfunc='unique'),
                                    station_abbreviation     = pd.NamedAgg(column='station_abbreviation',      aggfunc='unique'),
                                    alternative_name         = pd.NamedAgg(column='alternative_name',          aggfunc='unique'),
                                    station_crs              = pd.NamedAgg(column='station_crs',               aggfunc='unique'),
                                    longitude                = pd.NamedAgg(column='longitude',                 aggfunc='unique'),
                                    latitude                 = pd.NamedAgg(column='latitude',                  aggfunc='unique'),
                                    local_gravity            = pd.NamedAgg(column='local_gravity',             aggfunc='unique'),
                                    station_type             = pd.NamedAgg(column='station_type',              aggfunc='unique'),
#                                    platform_type            = pd.NamedAgg(column='platform_type',             aggfunc='unique'),
                                    platform_sub_type        = pd.NamedAgg(column='platform_sub_type',         aggfunc='unique'),
                                    operating_institute      = pd.NamedAgg(column='operating_institute',       aggfunc='unique'),
                                    operating_territory      = pd.NamedAgg(column='operating_territory',       aggfunc='unique'),
                                    city                     = pd.NamedAgg(column='city',                      aggfunc='unique'),
                                    contact                  = pd.NamedAgg(column='contact',                   aggfunc='unique'),
                                    role                     = pd.NamedAgg(column='role',                      aggfunc='unique'),
                                    observing_frequency      = pd.NamedAgg(column='observing_frequency',       aggfunc='unique'),
                                    reporting_time           = pd.NamedAgg(column='reporting_time',            aggfunc='unique'),
                                    telecommunication_method = pd.NamedAgg(column='telecommunication_method',  aggfunc='unique'),
                                    station_automation       = pd.NamedAgg(column='station_automation',        aggfunc='unique'),
                                    measuring_system_model   = pd.NamedAgg(column='measuring_system_model',    aggfunc='unique'),
                                    measuring_system_id      = pd.NamedAgg(column='measuring_system_id',       aggfunc='unique'),
                                    observed_variables       = pd.NamedAgg(column='observed_variables',        aggfunc='unique'),
                                    comment                  = pd.NamedAgg(column='comment',                   aggfunc='unique'),
                                    optional_data            = pd.NamedAgg(column='optional_data',             aggfunc='unique'),
                                    metadata_contact         = pd.NamedAgg(column='metadata_contact',          aggfunc='unique'),
                                    metadata_contact_role    = pd.NamedAgg(column='metadata_contact_role',     aggfunc='unique'))

    # flatten
    summary.reset_index(inplace=True)

    # need to process observed_variables
    summary['observed_variables'] = summary['observed_variables'].apply( lambda x: pd.Series((','.join(x)).split(',')).unique() )
    # now remove any empty entries and sort on numeric
    summary['observed_variables'] = summary['observed_variables'].apply(lambda x: sorted(list( filter(None, x) ),key=int ) )
    # now convert back to string (array brackets added after next step)
    #summary['observed_variables'] = summary['observed_variables'].apply(lambda x: '{' + ','.join(x) + '}' )
    summary['observed_variables'] = summary['observed_variables'].apply(lambda x: ','.join(x)  )


    # alternative name may be list ['name1,name2,name2', 'name4,name5']
    # convert to comma seperated string, split and get list of unique values
    summary['alternative_name'] = summary['alternative_name'].apply( lambda x: pd.Series((','.join(x)).split(',')).unique() )
    # now convert list back to single string
    summary['alternative_name'] = summary['alternative_name'].apply( lambda x: ','.join(x) )

    # check whether we have more than 1 station name, if so copy addition to alternative names
    summary['station_name'].apply( lambda x: list( filter(None, x) ) )
    mask = summary['station_name'].apply(lambda x: True if ( (len(x) > 1) and (isinstance(x, list)) ) else False )
    alt_mask = summary['alternative_name'].apply(lambda x: True if ( (len(x) > 1) and (isinstance(x, list)) ) else False )
    
    print(mask)
    if mask.any():
        #summary.at[mask, 'alternative_name'] = summary.loc[mask, 'station_name'].apply(lambda x: '{' + ','.join(x[1:]) + '}' )
        summary.at[mask, 'alternative_name'] = summary.loc[mask, 'station_name'].apply(lambda x: ','.join(x[1:]) ) + ',' + summary.loc[mask, 'alternative_name']
        summary.at[mask, 'station_name'] = summary.loc[mask, 'station_name'].apply(lambda x: x.item(0))
    else:
        # convert station name and alternative name to scalar
        summary['station_name'] = summary['station_name'].apply( lambda x: x.item(0) )    


    # remove NAs 
    mask = summary['platform_sub_type'].apply( lambda x: len(x) > 1) 
    summary.at[mask,'platform_sub_type'] = summary.loc[mask,'platform_sub_type'].apply( lambda x: pd.Series(x).dropna().unique() )

    # check unique columns only have one entry
    unique_check = ['secondary_id', 'secondary_id_scheme', 'station_abbreviation', 'station_crs', 'longitude', 'latitude',
        'local_gravity', 'station_type', 'platform_sub_type',
        'operating_institute', 'operating_territory', 'city', 'contact', 'role', 'observing_frequency',
        'reporting_time', 'telecommunication_method', 'station_automation', 'measuring_system_model',
        'measuring_system_id', 'comment', 'optional_data',
        'metadata_contact', 'metadata_contact_role']

    # *****
    # *****
    #
    # need to accomodate earlier data and station record numbers
    #
    # *****
    # *****

    for field in unique_check:
        print( field )
        print( summary.loc[ summary[field].apply( lambda x: len(x) ) > 1, field ] )
        assert  (max( summary[field].apply( lambda x: len(x) ) ) ) == 1
        # now convert to scalar
        summary[field] = summary[field].apply( lambda x: x.item() )



    field_order = ['primary_station_id', 'primary_station_id_scheme', 'station_record_number', 'secondary_id', 'secondary_id_scheme',
                       'station_name', 'station_abbreviation', 'alternative_name', 'station_crs', 'longitude', 'latitude',
                       'local_gravity', 'start_date', 'end_date', 'station_type', 'platform_type', 'platform_sub_type',
                       'operating_institute', 'operating_territory', 'city', 'contact', 'role', 'observing_frequency',
                       'reporting_time', 'telecommunication_method', 'station_automation', 'measuring_system_model',
                       'measuring_system_id', 'observed_variables', 'comment', 'optional_data', 'bbox_min_lon',
                       'bbox_max_lon', 'bbox_min_lat', 'bbox_max_lat', 'metadata_contact', 'metadata_contact_role']

    outfile = work_directory + './stations_annual-{:04d}.csv'.format( iyear )
    summary[field_order].to_csv(outfile,sep='|',index=False, na_rep='NULL')

if __name__ == '__main__':
    main(sys.argv[1:])
