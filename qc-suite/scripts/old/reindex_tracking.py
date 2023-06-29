import pandas as pd
import argparse
import sys
from pathlib import Path
import math


def main(argv):

    parser = argparse.ArgumentParser(description='Process MOQC tracking files')
    parser.add_argument('-lotus_id', dest='lotus_id', type=int, required=True, help='LOTUS job ID')
    parser.add_argument('-jobindex', dest='jobindex', type=int, required=True, help='Job index')
    parser.add_argument('-poolsize', dest='poolsize', type=int, required=True, help='Number of workers')
    parser.add_argument('-source', dest='source', required=True, help='Source data base directory')
    parser.add_argument('-destination', dest='dest', required=True, help = 'Directory to write to')

    args = parser.parse_args()
    poolsize = args.poolsize
    jobindex = args.jobindex - 1

    # get list of files and sort
    entries = list(Path(args.source).glob('**/*.csv'))
    filelist = []
    for entry in entries:
        if 'edge_case' not in str(entry):
            filelist.append((str(entry)))
    filelist.sort()
    nfiles = len(filelist)


    jobs_per_worker = math.ceil(nfiles / poolsize) + 1
    print(jobs_per_worker)
    job_offset = jobs_per_worker * jobindex

    lotus_id = args.lotus_id
    jobids = pd.np.arange(job_offset, job_offset + jobs_per_worker, 1)

    outdir = args.dest

    to_remove = list(Path(outdir).glob('**/*-*-{}.csv'.format(int(lotus_id))))
    print(to_remove)
    for p in to_remove:
        p.unlink( )


    # loop over each job processing every nth job
    for jdx in jobids:
        if jdx >= nfiles:
            break
        infile = filelist[jdx]
        try:
            datain = pd.read_csv(infile, dtype='object')
        except:
            print('Error reading{}'.format(infile))
            continue
        columns_out = list(datain.columns)
        outfile = datain.apply(lambda x: '{:04d}-{:02d}-{}.csv'.format(int(x['YR']), int(x['MO']), int(lotus_id)),
                               axis=1)
        datain = datain.assign(outfile=outfile)
        outfiles = datain['outfile'].unique()
        for of in outfiles:
            if (Path(outdir + of).is_file()):
                write_mode = 'a'
                write_headers = False
            else:
                write_mode = 'w'
                write_headers = True
            fh = open(outdir + of, mode=write_mode)
            to_save = datain.loc[datain['outfile'] == of, columns_out]
            to_save.to_csv(fh, index=False, header=write_headers)
            fh.close()


if __name__ == '__main__':
    main(sys.argv[1:])

