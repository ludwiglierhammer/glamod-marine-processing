from pub47 import *
import os
import pandasvalidation as pv
from dateutil.relativedelta import relativedelta
import datetime
from soundex import *
import argparse
import sys


def main(argv):

    parser = argparse.ArgumentParser(description='Split WMO Publication 47 metadata files by country')
    parser.add_argument( "-config", dest = "config", required = False, \
                          default = "config.json", help = "JSON file containing configuration settings")
    parser.add_argument( "-jobs", dest = "jobs", required = True, \
                          default = "jobs.json", help = "JSON file containing list of jobs to run")
    parser.add_argument( "-start", dest="jobIndexStart", type=int, required=True, default=1, \
                         help = "Index of first job to process")
    parser.add_argument( "-end", dest="jobIndexEnd", type=int, required=False, default=None, \
                         help = "Index of last job to process, defaults to first job")
    parser.add_argument( "-log", dest="log_path", required=False, default='./', \
                         help = "Directory to write log files to")
    parser.add_argument( "-tag", dest="tag", required=False, default='', \
                         help = "Tag appended to log files")

    args = parser.parse_args()
    control_file = args.jobs
    first_job = args.jobIndexStart
    last_job = args.jobIndexEnd
    config_file = args.config
    log_path = args.log_path

    if last_job is None:
        last_job = first_job

    # set validity periods for different editions
    validity = {'annual': 12, 'quarterly': 3, 'semi-annual': 6}


    # global options stored in config file
    # jobs specific options in control_file (need to rename)


    # load config options
    with open(config_file) as cf:
        config = json.load(cf)

    # load controls / list if files to process
    with open(control_file) as s:
        control = json.load(s)

    # parsing using pandas

    # global options

    map_path    = config['mapping_path']
    datapath         = config['data_path']
    configpath       = config['config_path']
    verbose          = config['verbose']
    outputpath       = config['output_path']
    corrections_file = configpath + './' + config['corrections_file']

    print(corrections_file)

    # read options from control file
    log_file = log_path + './split_pub47_' + args.tag + '.log'

    # load corrections
    with open(corrections_file) as m:
        corrections = json.load(m)

    # open log file for later use
    log = open(log_file, 'w')

    # iterate over jobs in control file
    for job_index in pd.np.arange( first_job, last_job + 1, 1):
        # find job in job list
        for job in control['jobs']:
            if job['jobindex'] == job_index:
                break
        assert job_index == job['jobindex']

        rejects = pd.DataFrame()

        # load schema
        schema = pub47schema( configpath + './schemas/' , job['schema'] )

        # get input file
        input_file  = job['data_file']
        input_file = datapath + input_file

        # set validity dates
        valid_from = datetime.date( job['year'] , job['month'] , 1)
        valid_to   = datetime.date( job['year'] , job['month'] , 1) + relativedelta( months = validity[job['freq']] )

        # feedback
        if verbose > 0:
            print("Processing " + os.path.basename(input_file) , file = log)

        # now read in the data
        datain = pub47load( schema, input_file, map_path )

        # remove any exact duplicates
        datain = datain.drop_duplicates( keep = 'first' )

        # now we need to identify duplicates within country
        id_counts = datain.loc[:, 'call'].value_counts()
        duplicated_ids = id_counts.index.values[id_counts > 1]
        duplicated_ids = list(duplicated_ids[duplicated_ids != cmiss])
        unique_ids = list(id_counts.index.values[id_counts == 1])
        unique_ids.append(cmiss)
        unique_rows = datain.loc[datain['call'].apply(lambda x: x in unique_ids), :].copy()

        for dup_id in duplicated_ids:
            dup_rows = datain.loc[datain['call'] == dup_id, :]
            # more than two entries for same callsign, reject all for later assessment
            if dup_rows.shape[0] > 2:
                rejects = pd.concat([rejects, dup_rows], ignore_index=True, sort=False)
                continue
            cmp = dup_rows.apply(lambda x: pub47_record_completeness(x), axis=1)
            vsslM = dup_rows.loc[:, 'vsslM']
            most_complete = list(cmp[cmp == max(cmp)].index.values)
            highest_class = list(vsslM[vsslM == min(vsslM)].index.values)
            ix = dup_rows.index.values
            same_name = soundex(dup_rows.loc[ix[0], 'name']) == soundex(dup_rows.loc[ix[1], 'name'])
            same_country = dup_rows.loc[ix[0], schema.recruiting_country ] == \
                           dup_rows.loc[ix[1], schema.recruiting_country ]
            # if same country and name merge if possible
            # if different country but same name use highest VOS class
            # else mark for rejection as ambiguous
            if same_country and same_name:
                # check if we can merge
                if pub47_record_compare(dup_rows.loc[ix[0], schema.duplicate_check],
                                        dup_rows.loc[ix[1], schema.duplicate_check]):
                    record_to_add = dup_rows.loc[[most_complete[0]],].copy()
                    merged_record = pub47_merge_rows(dup_rows.loc[ix[0], schema.duplicate_check],
                                                     dup_rows.loc[ix[1], schema.duplicate_check])
                    # record_to_add.at[ ix[0], schema['duplicate_check'] ] \
                    merged_record = pd.DataFrame(merged_record).transpose()
                    record_to_add.reset_index(inplace=True, drop=True)
                    merged_record.reset_index(inplace=True, drop=True)
                    record_to_add.at[:, schema.duplicate_check ] = merged_record.loc[:, schema.duplicate_check ]
                elif len(highest_class) == 1:
                    record_to_add = dup_rows.loc[[highest_class[0]], :].copy()
                elif len(most_complete) == 1:
                    record_to_add = dup_rows.loc[[most_complete[0]], :].copy()
                else:
                    rejects = pd.concat([rejects, dup_rows], ignore_index=True, sort=False)
                    record_to_add = None
            elif same_country :
                rejects = pd.concat([rejects, dup_rows], ignore_index=True, sort=False)
                record_to_add = None
            else:
                record_to_add = dup_rows
            if record_to_add is not None:
                unique_rows = pd.concat([unique_rows, record_to_add], ignore_index=True, sort=False)

        # save rejects to file
        print( "Saving rejects" )
        rejects = rejects.astype(str)
        rejects.replace(str(fmiss), pd.np.nan, inplace=True)
        rejects.replace(str(imiss), pd.np.nan, inplace=True)
        rejects.to_csv( outputpath + './split/' + os.path.basename(input_file) + '.' + 'reject', index=False, sep='|', na_rep='NULL')
        datain = unique_rows.copy()

        # get list of countries present in file
        countries = datain.rcnty.unique()
        print( countries , file = log)

        # now loop over countries homogenising
        for country in countries:
            if verbose > 0:
                print("Processing {}".format(country) , file = log)
            tmp_data = datain.loc[datain.rcnty == country].copy()

            tmp_data = tmp_data.reindex()
            nrows = tmp_data.shape[0]

            # output file for data from this country
            country_file = os.path.basename(input_file) + '.' + country

            cor = None
            # check if corrections exists for country / edition
            for cor_temp in corrections:
                if cor_temp['file'] == country_file:
                    cor = cor_temp
                    break

            # validate (and correct) data
            for column in tmp_data:
                # ++++++++++ CORRECT DATA ++++++++++
                # check if correction required and apply
                if cor is not None:
                    for f in cor['corrections']:
                        if f['field'] == column:
                            if f['all'] == 1:
                                if verbose > 0:
                                    print("Applying corrections to all values in {}".format(column)  , file = log)
                                    print("Factor = {}".format( f['factor'] ) , file = log)
                                # getting non missing rows
                                valid = tmp_data[column] != fmiss
                                # apply to tmp data
                                tmp_data.at[valid,column] = tmp_data.loc[valid,column] * f['factor']
                                # apply to datain
                                datain.at[ (datain['rcnty'] == country) & (valid) , column] = \
                                                datain.loc[ (datain['rcnty'] == country) & (valid) , column] * f['factor']
                            else:
                                valid = pv.validate_numeric(tmp_data[column], min_value=schema.column_valid_min[column],
                                                            max_value=schema.column_valid_max[column],
                                                            return_type='mask_series')
                                valid = valid & ~ ( tmp_data[column] == fmiss  )
                                if any(valid) :
                                    if verbose > 0:
                                        print("Applying corrections to invalid values in {}".format(column) , file = log)
                                        print("Factor = {}".format(f['factor']) , file = log)
                                    # apply to tmp data
                                    tmp_data.at[ valid, column ] = tmp_data.loc[ valid, column ] * f['factor']
                                    # now apply to datain
                                    valid = pv.validate_numeric(datain[column], min_value=schema.column_valid_min[column],
                                                                max_value=schema.column_valid_max[column],
                                                                return_type='mask_series')
                                    datain.at[ (datain['rcnty'] == country) & (valid), column] = \
                                                    datain.loc[ (datain['rcnty'] == country) & (valid), column] * f['factor']
                # ++++++++++ VALIDATE CODED DATA ++++++++++
                # get code table to validate against
                tableID = schema.column_code_table[ column ]
                if tableID in schema.code_tables:
                    codes = schema.code_tables[ tableID ]
                    if verbose > 1:
                        print("Validating against code table: " + str(tableID)  , file = log)
                    whitelist = codes['code'].map(str)
                    whitelist = whitelist.append( pd.Series([cmiss,'-1','NA','-999999']) )
                    tmp_values = tmp_data[column].map( str )
                    valid = pv.validate_string(tmp_values, whitelist=whitelist, return_type = 'mask_series')

                # ++++++++++ VALIDATE NUMERIC ++++++++++
                if tableID == None:
                    if schema.column_type[column] != 'object':
                        # if int convert to float and replace -1 with np.na
                        if str(tmp_data[column].dtype) == 'int64':
                            tmp_values = pd.to_numeric( tmp_data[column] )
                            tmp_values = tmp_values.replace( to_replace = imiss , value = fmiss) # pd.np.nan )
                        else:
                            tmp_values = tmp_data[column]
                        valid = pv.validate_numeric( tmp_data[column], min_value=schema.column_valid_min[column],
                                                     max_value=schema.column_valid_max[column],
                                                     return_type = 'mask_series')
                        valid = valid & ~ ( tmp_data[column].apply(lambda x: x == fmiss ) )
                    else:
                        valid = pd.Series( False * nrows )

                # calculate fraction bad
                fraction_bad = sum(valid) / nrows
                if (fraction_bad > 0.05) & (nrows > 10):
                    mask = valid.apply( lambda x: not x )
                    print( "///////////// "+  os.path.basename(input_file) + '.' + country + " /////////////", file = log)
                    print( "Large number of bad values for " + column + "(" + str(tableID) + ")" , file = log)
                    print( tmp_data.loc[ valid, column ].unique() , file = log)
                elif any(valid) :
                    print( "Bad values, {} ({})  :: {}".format( column, str(tableID), tmp_values[ valid ].unique()  ) ,
                           file = log)

            dataout = datain[datain.rcnty == country]
            dataout = dataout.assign(valid_from=valid_from)
            dataout = dataout.assign(valid_to=valid_to)
            dataout = dataout.assign(schema = schema.version)
            # convert all columns to object and replace fmiss and imiss with NA
            dataout = dataout.astype(str)
            dataout.replace( str(fmiss), pd.np.nan , inplace=True)
            dataout.replace( str(imiss), pd.np.nan, inplace=True)
            dataout.to_csv(outputpath + './split/' + os.path.basename(input_file) + '.' +
                           country, index=False, sep='|',na_rep='NULL')

if __name__ == '__main__':
    main(sys.argv[1:])