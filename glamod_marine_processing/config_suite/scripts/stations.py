"""Configuration stations package."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

from .modules.imma_noc import imma

imiss = -999999
fmiss = -999999.0
cmiss = "MSNG"

pd.options.display.max_columns = 100


class smart_dict(dict):
    """Class for smarter python dictionary."""

    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        """Get key value."""
        val = dict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        """Set key-value pair."""
        dict.__setitem__(self, key, val)

    def __missing__(self, val):
        """Set empty value to NULL."""
        if val == "":
            val = cmiss
        return val


def main(argv):
    """Main configuration stations function."""
    parser = argparse.ArgumentParser(
        description="Summarise stations for given month / year based on CDM file"
    )

    parser.add_argument(
        "-schema",
        dest="schema",
        required=True,
        help="JSON file containing schema for IMMA format",
        default=None,
    )
    parser.add_argument(
        "-code_tables",
        dest="code_tables",
        required=True,
        help="Directory containing code tables for IMMA format",
        default=None,
    )
    parser.add_argument(
        "-pub47file",
        dest="pub47file",
        required=True,
        help="Master file containing pub47 data",
        default=None,
    )
    parser.add_argument(
        "-mapping",
        dest="mapping",
        required=True,
        help="Mapping for pub47 to cdm",
        default=None,
    )
    parser.add_argument(
        "-index",
        dest="index",
        required=True,
        default=None,
        type=int,
        help="Index of month to process, month 1 = Jan 1946",
    )
    parser.add_argument(
        "-imma_source",
        dest="source",
        required=True,
        default=None,
        help="Directory containing original IMMA data",
    )
    parser.add_argument(
        "-cdm_source",
        dest="level2",
        required=True,
        default=None,
        help="Directory containing CDM formatted data to summarise",
    )
    parser.add_argument(
        "-destination",
        dest="destination",
        required=True,
        default=None,
        help="Target directory to write data to",
    )
    args = parser.parse_args()

    # load metadata (constant for all files)
    pub47file = (
        args.pub47file
    )  # '/group_workspaces/jasmin2/glamod_marine/data/r092019/wmo_publication_47/master/master_all.csv'
    wmo47 = pd.read_csv(pub47file, sep="|", dtype="object", low_memory=False)
    map_path = (
        args.mapping
    )  # '/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/metadata-suite/config/cdm_mapping/'

    # apply final mappings between code tables
    # 'meteorological_vessel_type':'vsslM', -> station_configuration_codes
    columns = ["observing_frequency", "automation", "recruiting_country", "vessel_type"]
    for column in columns:
        map_file = map_path + "./" + column + ".json"
        assert os.path.isfile(map_file)
        with open(map_file) as m:
            mapping = json.load(m)
        # mapping data stored as list of dicts (unfortunately), need to convert to single dict
        # (sub-class returns key if not in dict)
        m = smart_dict()
        for item in mapping["map"]:
            for key in item:
                m[key] = item[key]
        wmo47[column] = wmo47[column].map(m)

    wmo47 = wmo47.assign(idxKey=wmo47["callsign"] + "-" + wmo47["record_number"])
    wmo47.set_index("idxKey", inplace=True)

    datadir = (
        args.level2
    )  # '/group_workspaces/jasmin2/glamod_marine/data/r092019/ICOADS_R3.0.0T/level2/'
    idx = args.index - 1
    mm = pd.np.arange(732)
    dates = list(dt.datetime(1950, 1, 1) + relativedelta(months=m) for m in mm)
    d = dates[idx]

    iyear = d.year
    imonth = d.month

    print(f"Processing {iyear:04d}-{imonth:02d}")

    files = Path(datadir).glob(f"**/header-{iyear:04d}-{imonth:02d}-*.psv")
    files = (file for file in files if "excluded" not in str(file))
    datain = None
    for file in files:
        print(str(file))
        tmp = pd.read_csv(file, sep="|", dtype="object")
        # convert report_timestamp to date
        tmp["report_timestamp"] = pd.to_datetime(tmp["report_timestamp"])
        tmp["longitude"] = pd.to_numeric(tmp["longitude"])
        tmp["latitude"] = pd.to_numeric(tmp["latitude"])
        tmp["primary_station_id"] = tmp["primary_station_id"].str.upper()
        if datain is None:
            datain = tmp.copy()
        else:
            datain = pd.concat([datain, tmp])

    # now load IMMA file for month and merge certain fields with datain to determine observed variables
    # initialise IMMA reader
    icoads_dir = (
        args.source
    )  # '/group_workspaces/jasmin2/glamod_marine/data/datasets/ICOADS_R3.0.0T_original/'
    filename = icoads_dir + f"IMMA1_R3.0.0T_{iyear:04d}-{imonth:02d}"
    input_schema = (
        args.schema
    )  # '/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/' \
    #  + 'config-suite/config/schemas/imma/imma.json'
    code_tables = (
        args.code_tables
    )  # '/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/' \
    # + 'config-suite/config/schemas/imma/code_tables/'

    imma_obj = imma(
        schema=input_schema, code_tables=code_tables, sections=["core", "ATTM98"]
    )
    imma_obj.loadImma(filename, sections=["core", "98"], verbose=True, block_size=None)

    # print( datain )

    # add index to datain
    datain.set_index("source_record_id", inplace=True)

    # same for imma data
    imma_obj.data.set_index("attm98.uid", inplace=True)

    # merge datain and icoads_obj on icoads UID
    datain = pd.merge(
        datain, imma_obj.data, how="left", left_index=True, right_index=True
    )

    # output_schema = ''

    # load output schema
    # with open(output_schema) as s:
    #    output = json.load(s, object_pairs_hook=OrderedDict)

    # aggregate on id and id number (platform type included due to some ships with buoy like numbers)
    # first we need to enter value for those group variables with a missing value

    datain.fillna("NULL", inplace=True)
    # fields_with_missing = ['primary_station_id', 'station_record_number','platform_type','station_type', 'station_name','platform_sub_type']
    # datain[ fields_with_missing ] = datain[ fields_with_missing ].fillna('NULL')

    # need to convert n, ww, d to numeric and replace -99999 with nan
    datain[["core.n", "core.ww", "core.d"]] = datain[
        ["core.n", "core.ww", "core.d"]
    ].replace(-99999, pd.np.nan)

    # drop platform types that we are not processing
    selected_pts = ["", "0", "1", "2", "3", "4", "5", "7", "33"]
    pt_mask = datain["platform_type"].apply(lambda x: x in selected_pts)
    datain = datain[pt_mask].copy()

    # print(datain)

    # for column in datain:
    #    print( column )
    #    print( datain[column].unique() )

    stations_grouped = datain.groupby(
        [
            "primary_station_id",
            "primary_station_id_scheme",
            "station_record_number",
            "platform_type",
            "station_type",
            "station_name",
            "platform_sub_type",
        ]
    )
    summary = stations_grouped.agg(
        start_date=pd.NamedAgg(column="report_timestamp", aggfunc="min"),
        end_date=pd.NamedAgg(column="report_timestamp", aggfunc="max"),
        bbox_min_lon=pd.NamedAgg(column="longitude", aggfunc="min"),
        bbox_max_lon=pd.NamedAgg(column="longitude", aggfunc="max"),
        bbox_min_lat=pd.NamedAgg(column="latitude", aggfunc="min"),
        bbox_max_lat=pd.NamedAgg(column="latitude", aggfunc="max"),
        at_count=pd.NamedAgg(column="core.at", aggfunc="count"),
        sst_count=pd.NamedAgg(column="core.sst", aggfunc="count"),
        wbt_count=pd.NamedAgg(column="core.wbt", aggfunc="count"),
        dpt_count=pd.NamedAgg(column="core.dpt", aggfunc="count"),
        w_count=pd.NamedAgg(column="core.w", aggfunc="count"),
        d_count=pd.NamedAgg(column="core.d", aggfunc="count"),
        ww_count=pd.NamedAgg(column="core.ww", aggfunc="count"),
        n_count=pd.NamedAgg(column="core.n", aggfunc="count"),
        slp_count=pd.NamedAgg(column="core.slp", aggfunc="count"),
        obs_count=pd.NamedAgg(column="longitude", aggfunc="count"),
    )

    # flatten / reset index
    summary.reset_index(inplace=True)

    summary = summary.assign(observed_variables="")
    varNums = {
        "at": 85,
        "sst": 95,
        "wbt": 41,
        "slp": 58,
        "w": 107,
        "d": 106,
        "dpt": 36,
        "n": 21,
        "ww": 102,
    }
    for key in varNums:
        varname = key + "_count"
        mask = (100 * (summary[varname] / summary["obs_count"])) > 20
        summary.at[mask, "observed_variables"] = (
            summary.loc[mask, "observed_variables"] + str(varNums[key]) + ","
        )

    summary.observed_variables = summary.observed_variables.apply(lambda x: x[:-1])
    # summary.observed_variables = summary.observed_variables.apply( lambda x: '{' + x + '}' )
    summary = summary.assign(
        key=summary["primary_station_id"] + "-" + summary["station_record_number"]
    )
    summary = summary.assign(secondary_id="NULL")
    summary = summary.assign(secondary_id_scheme="NULL")
    summary = summary.assign(station_abbreviation="NULL")
    summary = summary.assign(alternative_name="NULL")
    summary = summary.assign(station_crs=0)
    summary = summary.assign(longitude="NULL")
    summary = summary.assign(latitude="NULL")
    summary = summary.assign(local_gravity="NULL")
    summary = summary.assign(operating_institute="NULL")
    summary = summary.assign(city="NULL")
    summary = summary.assign(contact="{}")
    summary = summary.assign(role="{}")
    summary = summary.assign(reporting_time="NULL")
    summary = summary.assign(telecommunication_method="NULL")
    summary = summary.assign(measuring_system_id="NULL")
    summary = summary.assign(
        comment="NOTE: not all variables have been ingested into the data store"
    )
    summary = summary.assign(optional_data=0)
    summary = summary.assign(metadata_contact="{1}")
    summary = summary.assign(metadata_contact_role="{5}")
    summary.set_index("key", inplace=True)
    summary = pd.merge(summary, wmo47, how="left", left_index=True, right_index=True)

    field_map = {
        "primary_station_id": "primary_station_id",
        "primary_station_id_scheme": "primary_station_id_scheme",
        "station_record_number": "station_record_number",
        "secondary_id": "secondary_id",
        "secondary_id_scheme": "secondary_id_scheme",
        "station_name": "station_name",
        "station_abbreviation": "station_abbreviation",
        "alternative_name": "alternative_name",
        "station_crs": "station_crs",
        "longitude": "longitude",
        "latitude": "latitude",
        "local_gravity": "local_gravity",
        "start_date": "start_date",
        "end_date": "end_date",
        "station_type": "station_type",
        "platform_type": "platform_type",
        "platform_sub_type": "platform_sub_type",
        "operating_institute": "operating_institute",
        "recruiting_country": "operating_territory",
        "city": "city",
        "contact": "contact",
        "role": "role",
        "observing_frequency": "observing_frequency",
        "reporting_time": "reporting_time",
        "telecommunication_method": "telecommunication_method",
        "automation": "station_automation",
        "aws_model": "measuring_system_model",
        "measuring_system_id": "measuring_system_id",
        "observed_variables": "observed_variables",
        "comment": "comment",
        "optional_data": "optional_data",
        "bbox_min_lon": "bbox_min_lon",
        "bbox_max_lon": "bbox_max_lon",
        "bbox_min_lat": "bbox_min_lat",
        "bbox_max_lat": "bbox_max_lat",
        "metadata_contact": "metadata_contact",
        "metadata_contact_role": "metadata_contact_role",
    }

    summary = summary.rename(columns=field_map)

    field_order = [
        "primary_station_id",
        "primary_station_id_scheme",
        "station_record_number",
        "secondary_id",
        "secondary_id_scheme",
        "station_name",
        "station_abbreviation",
        "alternative_name",
        "station_crs",
        "longitude",
        "latitude",
        "local_gravity",
        "start_date",
        "end_date",
        "station_type",
        "platform_type",
        "platform_sub_type",
        "operating_institute",
        "operating_territory",
        "city",
        "contact",
        "role",
        "observing_frequency",
        "reporting_time",
        "telecommunication_method",
        "station_automation",
        "measuring_system_model",
        "measuring_system_id",
        "observed_variables",
        "comment",
        "optional_data",
        "bbox_min_lon",
        "bbox_max_lon",
        "bbox_min_lat",
        "bbox_max_lat",
        "metadata_contact",
        "metadata_contact_role",
    ]

    outfile = f"stations-{iyear:04d}-{imonth:02d}.csv"

    summary[field_order].to_csv(
        args.destination + "./" + outfile, index=False, sep="|", na_rep="NULL"
    )


if __name__ == "__main__":
    main(sys.argv[1:])
