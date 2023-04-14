from pub47 import *
import argparse
import sys

def main(argv):
    parser = argparse.ArgumentParser(description='Merge individual country metadata files to one master file')
    parser.add_argument("-config", dest="config", required=False, \
                        default="config.json", help="JSON file containing configuration settings")
    parser.add_argument("-countries", dest="country_file", required=False, \
                        help="JSON file containing list of countries to process", default=None)


    args = parser.parse_args()
    country_file = args.country_file
    config_file = args.config

    with open(config_file) as cf:
        config = json.load(cf)

    outputpath = config['output_path']

    # load list of countries to process
    with open(country_file) as m:
        countries = json.load( m )

    master_all = pd.DataFrame()

    # iterate over countries
    for country in countries :
        print( "Processing {}".format( country ) )
        # load data for country
        metadata = pd.read_csv( outputpath + './master/master.{}.csv'.format(country) , sep = '|' ,
                                low_memory=False, dtype='object')
        # append to master list
        master_all = pd.concat( [master_all, metadata ], sort = False )

    # convert valid to/from to dates
    master_all['valid_from'] = pd.to_datetime(master_all['valid_from'])
    master_all['valid_to'] = pd.to_datetime(master_all['valid_to'])

    # sort on callsign then valid_from
    master_all.sort_values(['callsign','valid_from'], inplace=True)
    master_all.reset_index(inplace=True, drop=True)

    # update record numbers
    master_all['record_number'] = master_all.groupby(['callsign']).cumcount()+1

    # now back to str and replace missing values
    master_all =  master_all.astype( str )
    master_all.replace( str(fmiss) , pd.np.nan, inplace = True)
    master_all.replace( str(imiss) , pd.np.nan, inplace = True)
    master_all.replace( 'nan', pd.np.nan, inplace=True)
    master_all.to_csv( outputpath + './master/master_all.csv', index=False, sep='|', header = True, na_rep='NULL')


if __name__ == '__main__':
    main(sys.argv[1:])
