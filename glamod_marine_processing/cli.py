import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

def add_options(*options):

    def _add_options(func):
        for option in reversed(*options):
            option = getattr(Options, option)
            func = option(func)
        return func

    return _add_options

class Options:

    def __init__(self):
        self.machine = click.option(
            "-m",
            "--machine",
            default="MELUXINA",
            help="""HPC cluster where to create and run the scripts,
            * KAY: kay.ichec.ie \n
            * MELUXINA: login.lxp.lu \n
            * default: MELUXINA
            """,
        )
        
        self.submit_jobs = click.option(
            "-submit", "--submit_jobs", is_flag=True, help="Submit job scripts"
        )
    
        self.level = click.option(
            "-l",
            "--level",
            required=True,
            help="""Step of observation suite process:

            * level1a: Mapping dataset to CDM. \n
            * level1b: Improve data with corrections and/or additional information. \n
            * level1c: Perform data validation and apply data with metadata.\n
            * level1d: Enrich data with external metadata. \n
            * level1e: Add quality control flags to data. \n
            * level2: Make data ready to ingest in the database.
            """,
        )

        self.release =  click.option(
            "-r", "--release", default="release_7.0", help="Name of the data release."
        )

        self.update = click.option(
            "-u", "--update", default="000000", help="Name of the data release update."
        )

        self.dataset = click.option(
            "-d",
            "--dataset",
            default="ICOADS_R3.0.2T",
            help="Name of the data release dataset.",
        )   
        self.previous_release = click.option(
            "-pr",
            "--previous_release",
            default="release_6.0",
            help="Name of the previous data release.",
        )
        
        self.split_files = click.option(
            "-split", "--split_files", is_flag=True, help="Step 1: Splitting PUB47 data files."
        )
        self.merge_countries = click.option(
            "-merge", "--merge_countries", is_flag=True, help="Step 2: Merge countries."
        )
        self.extract_for_cds = click.option(
            "-extract", "--extract_for_cds", is_flag=True, help="Step 3: Extract for CDS"
        )

        self.corrections_version = click.option(
            "-c",
            "--corrections_version",
            default="",
            help="Name of the NOC corrections version.",
        )

Options = Options()
