import argparse

def get_parser_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("positional", metavar="N", type=str, nargs="+")
    parser.add_argument("--failed_only")
    parser.add_argument("--remove_source")

    args = parser.parse_args()
    if args.failed_only:
        args.failed_only = True if args.failed_only == "yes" else False
        logging.warning("failed_only is currently deactivated, all data will be processed")
        # this is because of changes to the failed/success indicator used. config_array.main expects the
        # log files to be renamed to name.ok in case of success, instead of .success file created
        args.failed_only = False
    else:
        args.failed_only = False
        
    if args.remove_source:
        logging.warning('remove_source has been discontinued, source data will not be removed')
        #remove_source = True if args.remove_source== 'yes' else False
        args.remove_source = False
    else:
        args.remove_source = False
    return args