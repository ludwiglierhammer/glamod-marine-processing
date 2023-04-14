from pub47 import *
import os
import Levenshtein
from soundex import *
import argparse
import sys
import datetime as dt
from dateutil.relativedelta import relativedelta

# sub-class of dict to return key for missing values
class smart_dict(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)

    def __missing__(self, key):
        key = ''
        if key == '':
            key = cmiss
        return key


def main(argv):

    parser = argparse.ArgumentParser(description='Merge split WMO Publication 47 metadata files to one file per country')
    parser.add_argument( "-config", dest = "config", required = False, \
                          default = "config.json", help = "JSON file containing configuration settings")
    parser.add_argument( "-jobs", dest = "jobs", required = True, \
                          default = "jobs.json", help = "JSON file containing configuration and list of jobs to run")
    parser.add_argument("-countries", dest="country_file", required=False, \
                         help="JSON file containing list of countries to process", default = None)
    parser.add_argument("-index", dest="index", required=False,  type = int,  \
                         help="Index of country to process", default = None)
    parser.add_argument("-country", dest="country", required=False, \
                         help="2 character country code to process", default = None)

    #parser.add_argument( "-log", dest="log_path", required=False, default='./', \
    #                     help = "Directory to write log files to")
    #parser.add_argument( "-tag", dest="tag", required=False, default='', \
    #                     help = "Tag appended to log files")



    # add argument to specify index / position in list of countries.
    args = parser.parse_args()
    control_file = args.jobs
    config_file = args.config
    country_file = args.country_file
    country = args.country
    country_index = args.index - 1
    #log_path = args.log_path

    if country_file is None and country is None:
        print("Error, one of countries or country must be supplied")
        assert False

    if country_file is not None and country is not None:
        print("Error, only one of countries or country must be supplied")
        assert False

    # load config options
    with open(config_file) as cf:
        config = json.load(cf)

    with open(control_file) as s:
        control = json.load( s )

    #datapath         = config['data_path']
    configpath       = config['config_path']
    #verbose          = config['verbose']
    outputpath       = config['output_path']
    #corrections_file = configpath + './' + config['corrections_file']

    map_file = config["mapping_path"] + "./pub47_common_names.json"

    fmiss = -999999.
    imiss =  -1 # -999999

    with open(map_file) as m:
        mapping = json.load( m )

    if country_file is not None:
        with open(country_file) as m:
            countries = json.load( m )
        if country_index is not None:
            country = countries[ country_index ]
            countries = list()
            countries.append( country )
    else:
        countries = list()
        countries.append( country )

    # iterate over countries
    for country in countries:
        print( "Processing "  + country )
        master = pd.DataFrame()
        for job in control['jobs']:
            schema = pub47schema(configpath + './schemas/', job['schema'])
            input_file  = outputpath + './split/' + os.path.basename( job['data_file'] ) + "." + country

            # files now only exist for country if data in them, warn if no file found.
            if not os.path.isfile( input_file ):
                print( '{} not found'.format(input_file) )
                continue
            else:
                print(' ... {} '.format(input_file))
            # load data
            datain = pd.read_csv( input_file , sep = '|',  dtype='object') # read as object
            datain = datain.drop_duplicates(keep='first') # some duplicates are appearing from somewhere !
            # check whether we need to handle columns that have been split
            # split_columns = (len( schema.split_fields ) > 0)

            # NOTE: only text / object columns split so don't need to convert those columns
            # need to check / revise this in the future
            # convert to expected data type
            numeric_columns = list()
            columns_processed = list()
            for column in schema.column_name:
                columns_processed.append( column )
                if schema.column_type[ column ] == 'int':
                    datain[column].replace(cmiss, str(imiss), inplace=True)
                    datain = datain.astype({column: 'int'})
                elif schema.column_type[ column ] == 'float':
                    datain[column].replace(cmiss, str(fmiss), inplace=True)
                    datain = datain.astype({column: 'float'})
                    numeric_columns.append(column)

            # convert numeric_columns variable to set for later use
            numeric_columns = set( numeric_columns )

            # fill all NAs with fmiss (-99999)
            #datain.fillna( fmiss , inplace = True)

            # convert valid_from and valid_to to datetime objects, these are not in the schema but added in the first
            # step of processing
            datain['valid_from'] = pd.to_datetime( datain['valid_from'] )
            datain['valid_to'] = pd.to_datetime(datain['valid_to'])

            # identify which mapping to use
            version = "v" + str( schema.version )
            mapUse = mapping[ version ][1]
            invMap = dict([[v,k] for k,v in mapUse.items()])

            # map columns in input data to output required (store in tmp df)
            tmpDf = datain.copy()
            tmpDf = tmpDf.assign( source_file = input_file )
            tmpDf = tmpDf.assign( alt_names = '' )

            # check if year present, if not set to year from schema
            if not( 'year' in tmpDf) :
                tmpDf =tmpDf.assign(year  = job['year'])

            tmpDf = tmpDf.assign( month = job['month'] )
            tmpDf = tmpDf.assign( publication_frequency = job['freq'])

            # rename columns to that expected in output schema
            colNewNames = dict()
            for column in tmpDf:
                if column in invMap:
                    colNewNames[ column ] = invMap[ column ]

            tmpDf.rename( columns = colNewNames, inplace = True)

            # regularise ship names, first need to fill null strings with 'NULL'
            tmpDf['name'] = tmpDf['name'].fillna('NULL')
            # replace double spaces with single
            tmpDf.at[:, 'name'] = tmpDf.loc[:, 'name'].apply(lambda x: re.sub("\\s\\+", " ", x))
            # now single initials with initial., e.g. A with A.
            tmpDf.at[:, 'name'] = tmpDf.loc[:, 'name'].apply(lambda x: re.sub("( )([A-Z]{1})( )", "\\1\\2.\\3", x))
            # finally, add space between dot and letters, e.g. A.ABC with A. ABC
            tmpDf.at[:, 'name'] = tmpDf.loc[:, 'name'].apply(
                lambda x: re.sub("([A-Z]{1})(\\.)([A-Z]{1})", "\\1\\2 \\3", x))

            sx = tmpDf['name'].apply(lambda x: soundex(x))
            tmpDf = tmpDf.assign( sx = sx )
            tmpDf = tmpDf.assign(  record_number = 1)
            to_add = []
            # now check each callsign and ship name to see if records can be merged with existing
            if master.shape[0] > 0:
                print("   input_file: {}  ".format(input_file))
                print( tmpDf['callsign'].dtype )
                for idx in tmpDf.index.values:
                    action = 'new_record'
                    id = tmpDf.loc[idx, 'callsign']
                    if id == cmiss:
                        continue
                    shipname = tmpDf.loc[ idx , 'name']
                    matches = master.loc[ (master['callsign'] == id) ].copy()
                    if matches.shape[0] > 0:

                        # get last record added
                        max_record = max(matches['record_number'])
                        id_match = matches[ matches['record_number'] == max_record ].index.values

                        # now get similarity in names, either by soundex or type
                        distance = max( float(matches['sx'][id_match[0]] == tmpDf.loc[idx, 'sx' ]),\
                                        Levenshtein.ratio(matches['name'][id_match[0]], shipname) )

                        # if close match check elements
                        if distance > 0.8:
                            # get list of common fields between new entry and matches
                            common = list( set(list( tmpDf )).intersection( list( matches ) ).intersection( config['duplicateChecks']  )   )

                            # perform merge
                            # idx = row in current file
                            # id_match = row in master data frame

                            # if rows are the same excluding missing data, merge copying missing data
                            # else if rows are different add new row.

                            # get list of matching elements (TRUE|FALSE)
                            matching_elements = tmpDf.loc[idx, common ] == matches.loc[id_match[0], common]
                            # possible actions
                            #  - merge and fill
                            #  - merge and correct
                            #  - keep old, increment dates
                            #  - add new
                            if matching_elements.all() : # exact match, merge dates and files
                                action = 'increment_date'
                                min_date = min( {tmpDf.loc[ idx, 'valid_from'], matches.loc[id_match[0], 'valid_from']} )
                                max_date = max( {tmpDf.loc[ idx, 'valid_to' ], matches.loc[id_match[0], 'valid_to']} )
                                #master.at[matches.index[0], 'valid_to'] = max_date
                                #master.at[matches.index[0], 'valid_from'] = min_date
                                master.at[id_match[0], 'valid_to'] = max_date
                                master.at[id_match[0], 'valid_from'] = min_date
                                master.at[id_match[0], 'source_file'] = master.loc[id_match[0], 'source_file'] + ';' + tmpDf.loc[ idx, 'source_file' ]
                                if (tmpDf.loc[idx,'name'] != master.loc[id_match[0], 'name' ]) & (tmpDf.loc[idx,'name'] not in master.loc[id_match[0], 'alt_names']) :
                                    master.at[id_match[0], 'alt_names'] = master.loc[id_match[0], 'alt_names'] + ';' + tmpDf.loc[idx, 'name']
                            else:
                                # remove missing elements and recheck
                                missing_left = ( (tmpDf.loc[idx, common] == cmiss) | (tmpDf.loc[idx, common] == imiss ) | (tmpDf.loc[idx, common] == fmiss ) )
                                missing_right = ( (matches.loc[id_match[0], common] == cmiss) | (matches.loc[id_match[0], common] == imiss) | (matches.loc[id_match[0], common] == fmiss) )
                                missing = ( missing_left | missing_right )
                                missing = (missing | matching_elements)
                                if missing.all() :
                                    action = 'fill_missing'
                                    mismatch = ~ matching_elements
                                    right_columns = missing_right.index[ (missing_right & mismatch) ].format()
                                    # set valid date range to span both records
                                    min_date = min({tmpDf.loc[idx, 'valid_from'], matches.loc[id_match[0], 'valid_from']})
                                    max_date = max({tmpDf.loc[idx, 'valid_to'], matches.loc[id_match[0], 'valid_to']})
                                    master.at[id_match[0], 'source_file'] = master.loc[id_match[0], 'source_file'] + ';' + tmpDf.loc[idx, 'source_file']
                                    if (tmpDf.loc[idx, 'name'] != master.loc[id_match[0], 'name']) & (tmpDf.loc[idx, 'name'] not in master.loc[id_match[0], 'alt_names']):
                                        master.at[id_match[0], 'alt_names'] = master.loc[id_match[0], 'alt_names'] + ';' + tmpDf.loc[idx, 'name']
                                    # now update master table
                                    master.at[id_match[0], 'valid_to'] = max_date
                                    master.at[id_match[0], 'valid_from'] = min_date
                                    # now fill master table (this is the one we keep)
                                    if len(right_columns) > 0:
                                        master.at[ id_match[0], right_columns] = tmpDf.loc[ idx, right_columns ]
                                else:
                                    # now check numeric (float) elements
                                    mismatch = ~ (matching_elements | missing)
                                    numeric_mismatch = numeric_columns.intersection( mismatch.index[ mismatch ].format() )
                                    if len(numeric_mismatch) > 0 :
                                        print(" **** Numeric mismatch **** ")
                                        print(tmpDf.loc[idx, pd.np.array(common)[ mismatch ]])
                                        print(matches.loc[id_match[0], pd.np.array(common)[ mismatch ]])
                                        action = 'correct_numeric'
                                    else:
                                        action = 'new_record'
                                        tmpDf.at[idx, 'record_number'] = max_record + 1
                        else:
                            action = 'new_record'
                            tmpDf.at[idx, 'record_number'] = max_record + 1
                    if action == 'new_record':
                        to_add.append( idx )
            else:
                to_add = tmpDf.index.values
            # concat to master table
            master = pd.concat( [master, tmpDf.loc[ to_add,]], ignore_index=True, sort = False )
            # replace nans with expected missing value
            for column in master :
                if master[column].dtype == 'datetime64[ns]':
                    continue
                if master[column].dtype == 'float64' :
                    master[column].fillna( fmiss , inplace = True)
                elif master[column].dtype == 'object' :
                    master[column].fillna(cmiss, inplace=True)
                elif master[column].dtype == 'int64' :
                    master[column].fillna( imiss, inplace=True)
                else:
                    print('Unknown column type: {}'.format( master[column].dtype ))

        # final step is sort and addition of record numbers


        # assign UIDs to all records
        uid = master.apply( lambda x: '{}-{}-{}'.format( x['callsign'],x['sx'],x['recruiting_country']), axis = 1)
        master = master.assign( uid = uid )

        # sort by id then date
        master.sort_values(['uid','valid_from'], inplace=True)

        # reset index
        master.reset_index(inplace= True, drop=True)

        # now reset record numbers based on uid
        uids = master['uid'].unique()
        count = 0
        for uid in uids :
            if count % 200 == 0:
                print( '{} / {} '.format( count, len(uids) ) )
            records = master.loc[ master['uid'] == uid, : ]
            nrecs = records.shape[0]
            master.at[ records.index,'record_number'] = pd.np.arange( nrecs )
            # adjust valid from and to for 1st and last records
            new_valid_to = records.valid_from.shift(-1)
            to_change = (((records['valid_to'] - new_valid_to)).dt.days >= -3625) & \
                        (((records['valid_to'] - new_valid_to)).dt.days  <= 0)
            if to_change.any():
                records.loc[ to_change , 'valid_to'] = new_valid_to[ to_change ]
            # add 5 years to last record and subtract 1 year from first
            records.loc[ records.index[0] , 'valid_from' ] =  records.loc[records.index[0] , 'valid_from' ] - relativedelta(months=12)
            records.loc[ records.index[nrecs - 1], 'valid_to'] = records.loc[records.index[nrecs - 1], 'valid_to'] + relativedelta(months=60)
            master.at[ records.index, ['valid_from','valid_to'] ] =  records.loc[ records.index, ['valid_from','valid_to'] ]
            count += 1

        # now save
        # convert each field back to str and replace missing values with NULL
        master = master.astype( str )
        master.replace( str(fmiss), pd.np.nan , inplace = True)
        master.replace( str(imiss), pd.np.nan , inplace = True)
        master.to_csv(outputpath + './master/master.'+country+'.csv', index=False ,sep='|', na_rep = 'NULL' )

if __name__ == '__main__':
    main(sys.argv[1:])