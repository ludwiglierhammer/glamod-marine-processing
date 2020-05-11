from dateutil.relativedelta import relativedelta
import datetime as dt
import pandas as pd
import argparse
from pathlib import Path
import sys

def main(argv):
    # get arguments to process
    parser = argparse.ArgumentParser(description='Merge monthly MOQC tracking files')
    parser.add_argument('-index', dest='index', type=int, required=True, help='Month to process, 1 = Jan 1985')
    parser.add_argument('-source', dest='source', required=True, help='base directory')
    parser.add_argument('-dest', dest='dest', required=True, help='output directory')
    args = parser.parse_args()
    imonth = args.index - 1
    # generate list of months
    mm = pd.np.arange( 360 )
    dates = list( dt.datetime( 1985, 1 , 1) + relativedelta( months = m ) for m in mm )
    # now get month to process
    year = dates[imonth].year
    month = dates[imonth].month

    # get list of files to concatenate
    basepath = args.source # '/gws/nopw/j04/c3s311a_lot2/code/marine_code/dyb_tmp/tracking_sort/output/'
    pattern = '**/{:4d}-{:02d}-*.csv'.format(year, month)
    entries = list(Path(basepath).glob(pattern))
    outfile = '{:4d}-{:02d}.csv'.format(year, month)
    outdf = None

    for entry in entries:
        try:
            datain = pd.read_csv( entry, dtype='object' )
        except:
            print('Error reading {}'.format(entry) )
            continue
        if outdf is None:
            outdf = datain.copy()
        else:
            outdf = pd.concat([outdf, datain])

    outdf.sort_values('UID', inplace = True)
    outdf.to_csv( args.dest + outfile, index = False )

if __name__ == '__main__':
    main(sys.argv[1:])
