"""Quality control for IMMA NOC data."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
from collections import OrderedDict
from datetime import datetime

import pandas as pd
import pandasvalidation as pv
from dateutil.relativedelta import relativedelta

# add to imma_obj in future
imiss = -99999
fmiss = pd.np.nan
cmiss = "__EMPTY"
tmiss = pd.NaT

attmIndex = [
    "core",
    " 1",
    " 5",
    " 6",
    " 7",
    " 8",
    " 9",
    "95",
    "96",
    "97",
    "98",
    "99",
]

attmLength = [108, 65, 94, 68, 58, 102, 32, 61, 53, 32, 15, 0]

attmSentinals = [
    "",
    " 165",
    " 594",
    " 668",
    " 758",
    " 82U",
    " 932",
    "9561",
    "9653",
    "9732",
    "9815",
    "99 0",
]

attmBlanks = [
    s1 + s2
    for s1, s2 in zip(attmSentinals, list(map(lambda x: " " * (x - 4), attmLength)))
]

attmLength = dict(zip(attmIndex, attmLength))


# define functions
# ===========================
# functions for processing the different ICOADS data type
# ===========================
# convert character to int
def conv_int(value):
    """Convert to integer."""
    if len(value) == 0:
        return imiss
    else:
        return int(value)


# convert character to float
# ===========================
def conv_float(value):
    """Convert to float."""
    if len(value) == 0:
        return fmiss
    else:
        return float(value)


# ===========================
# convert character to object
def conv_object(value):
    """Convert to object."""
    if len(value) == 0:
        return cmiss
    else:
        return value


# ===========================
# convert character (b36) to int
# ===========================
def conv_base36(value):
    """Convert to BASE36 value."""
    if len(value) == 0:
        return imiss
    else:
        return int(value, 36)


# ===========================
def apply_scale(value, scale, msng):
    """Apply scale."""
    if value != msng:
        return value * scale
    else:
        return msng


def to_none(value):
    """Return missing values as None."""
    if (value == imiss) | (value == fmiss) | (value == cmiss) | (value == tmiss):
        return None
    else:
        return value


def to_datetime(series):
    """Convert pandas date columns to datetime object."""
    dates = {
        "year": series["core.yr"],
        "month": series["core.mo"],
        "day": series["core.dy"],
    }
    if pd.np.isnan(series["core.hr"]):
        dates["hour"] = 12
        add_hours = series["core.lon"] / 15
    else:
        hour = series["core.hr"]
        hour_floor = math.floor(hour)
        dates["hour"] = hour_floor
        dates["minute"] = round(60 * (hour - hour_floor))
        add_hours = False

    datetime_obj = datetime(**dates)
    if add_hours is not False:
        return datetime_obj + relativedelta(hours=add_hours)
    return datetime_obj


def to_datetime_str(series):
    """Convert pandas date columns to datetime string."""
    yr = series["core.yr"]
    mo = series["core.mo"]
    dy = series["core.dy"]
    return f"{yr}-{mo}-{dy}"


def to_position_str(series):
    """Convert pandas position columns to position string."""
    lon = round(series["core.lon"], 5)
    lat = round(series["core.lat"], 5)
    return f"POINT({lon} {lat})"


def to_180(series):
    """Convert longitude to between -180 and 180."""
    lon = series["core.lon"]
    if lon >= 180:
        return lon - 360
    return lon


def open_file(
    filename,
    zipped=True,
    encoding="utf-8",
):
    """Open file from disk."""
    if zipped is True:
        func = gzip.open
        args = ["r"]
    else:
        func = open
        args = []

    with func(filename, encoding=encoding, *args) as content_file:
        return content_file.read()


imma_converters = {
    "int": conv_int,
    "float": conv_float,
    "object": conv_object,
    "base36": conv_base36,
}


class imma:
    """Class for quakity control for IMMA data."""

    def __init__(
        self, schema, code_tables, sections=["core", "ATTM1", "ATTM98"], lower=True
    ):
        self.colNames = []
        self.colTypes = {}
        self.colWidths = []
        self.colScale = {}
        self.colMin = {}
        self.colMax = {}
        self.conv = {}
        self.codetable = {}
        self.cursor = 0
        self.number_records = 0
        self.content_buffer = None
        self.record_index = None
        with open(schema) as s:
            file_schema = json.load(s, object_pairs_hook=OrderedDict)
        for section in file_schema:
            if section in sections:
                for item in file_schema[section]:
                    # convert name to lower and prepend section
                    self.set_attributes(section, item, lower, code_tables)

    def set_attributes(self, section, item, lower, code_tables):
        """Set attributes."""
        if lower:
            item["name"] = section.lower() + "." + item["name"].lower()
        self.colNames.append(item["name"])
        self.colTypes[item["name"]] = item["kind"]
        self.colScale[item["name"]] = item["scale"]
        if self.colScale[item["name"]] is not None:
            self.colScale[item["name"]] = float(self.colScale[item["name"]])
        self.colMin[item["name"]] = item["min"]
        if self.colMin[item["name"]] is not None:
            self.colMin[item["name"]] = float(self.colMin[item["name"]])
        self.colMax[item["name"]] = item["max"]
        if self.colMax[item["name"]] is not None:
            self.colMax[item["name"]] = float(self.colMax[item["name"]])
        if (item["length"]) is None:
            item["length"] = 0
        self.colWidths.append(int(item["length"]))
        if item["codetable"] is not None:
            self.codetable[item["name"]] = code_tables + item["codetable"]
        else:
            self.codetable[item["name"]] = None
        self.conv[item["name"]] = imma_converters.get(self.colTypes[item["name"]])

    def md5(self, fname):
        """Return MD5 hash."""
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def numeric_scaling(self, series, scaling):
        """Apply scaling factor."""
        return series.apply(lambda x: apply_scale(x, scaling, fmiss))

    def numeric(self, series):
        """Replace missing values."""
        series = pd.to_numeric(series)
        # replace imiss with nans
        return series.replace(to_replace=imiss, value=fmiss)

    def to_str(self, series):
        """Convert numeric to string."""
        return series.map(round).map(str)

    def check_bad_data(self, data, column, check):
        """Check whether data is bad data."""
        if any(check):
            print(data.loc[check, column].unique())
            data.loc[check, "value_check"] = (
                data.loc[check, "value_check"] + ":" + column
            )
            data.loc[check, "bad_data"] = True
        return data

    def check_numeric_bad_data(self, data, column):
        """Check whether numeric data is bad data."""
        check = pv.validate_numeric(
            data[column],
            min_value=self.colMin[column],
            max_value=self.colMax[column],
            return_type="mask_series",
        )
        return self.check_bad_data(data, column, check)

    def check_string_bad_data(self, data, column):
        """Check whether string data is bad data."""
        valid_codes = pd.read_csv(self.codetable[column], sep="\t")
        white_list = valid_codes["code"]
        white_list = white_list.map(str)
        white_list = white_list.append(pd.Series([str(imiss, cmiss, str(fmiss))]))
        check = pv.validate_string(
            data[column], whitelist=white_list, return_type="mask_series"
        )
        return self.check_bad_data(data, column, check)

    def validation(self, data):
        """Apply scaling fsctor and validate data."""
        for column in data:
            if column == "value_check":
                continue
            elif column == "bad_data":
                continue
            elif column == "code_chcek":
                continue

            if (self.colTypes[column] == "float") & (self.colScale[column] is not None):
                data[column] = self.numeric_scaling(data[column], self.colScale[column])

            if (
                (self.colTypes[column] == "int")
                | (self.colTypes[column] == "base36")
                | (self.colTypes[column] == "float")
            ):
                data[column] = self.numeric(data[column])
                data = self.check_numeric_bad_data(data)

            if self.codetable[column] is not None:
                # load code table
                if (self.colTypes[column] == "int") | (
                    self.colTypes[column] == "base36"
                ):
                    data[column] = self.to_str(data[column])

                data = self.check_string_bad_data(data)
        return data

    def read_bufer(self, sections, block_size=None):
        """Read buffer to DataFrame."""
        if block_size is None:
            self.idx = list(range(self.number_records))
            self.cursor = self.number_records
        else:
            self.idx = list(
                range(self.cursor, min(self.cursor + block_size, self.number_records))
            )
            self.cursor = min(self.cursor + block_size, self.number_records)

        tmpDict = dict(zip(self.record_index[self.idx], self.content_buffer[self.idx]))

        read_buffer = io.StringIO("")
        outputKeys = sections

        for key in tmpDict:
            tmpDict2 = dict(zip(attmIndex, attmBlanks))
            tmpString = tmpDict[key]
            tmpDict2["core"] = tmpString[:108]
            tmpString = tmpString[108:]
            key2 = ""
            while (len(tmpString) > 1) & (key2 != "99"):
                key2 = tmpString[0:2]
                tmpDict2[key2] = tmpString[0 : attmLength[key2]]
                tmpString = tmpString[attmLength[key2] :]
            newString = ""
            # for key2 in attmIndex:
            for key2 in outputKeys:
                newString = newString + tmpDict2[key2]
            print(newString, file=read_buffer)

        read_buffer.seek(0)
        return pd.read_fwf(
            read_buffer,
            widths=self.colWidths,
            header=None,
            names=self.colNames,
            converters=self.conv,
        )

    def loadImma(
        self,
        filename,
        sections=["core", " 1", "98"],
        version=3,
        zipped=False,
        verbose=False,
        block_size=None,
        sort=False,
    ):
        """Load IMMA data."""
        if self.content_buffer is None:
            # read file into buffer
            try:
                content = open_file(filename, zipped=zipped, encoding="utf-8")
            except UnicodeDecodeError:
                print("Using cp1252 character set")
                content = open_file(filename, zipped=zipped, encoding="cp1252")
            except Exception:
                raise ("Error reading file: " + filename)

            self.content_buffer = pd.Series(list(io.StringIO(content)))
            if sort:
                sort_key = self.content_buffer.str.slice(34, 43)
                print(sort_key)
            self.record_index = self.content_buffer.index.values
            self.number_records = self.content_buffer.size

            if verbose:
                print(
                    "INFO ({}) .... Data read into memory, {} records to process.".format(
                        datetime.now().time().isoformat(timespec="milliseconds"),
                        self.number_records,
                    )
                )

        else:
            # check we have not read all data
            if self.cursor >= self.number_records:
                self.cursor = 0
                self.number_records = 0
                self.content_buffer = None
                self.record_index = None
                if verbose:
                    print(
                        "INFO ({}) .... End of file".format(
                            datetime.now().time().isoformat(timespec="milliseconds")
                        )
                    )
                return False

        self.data = self.read_buffer(sections, block_size=block_size)
        if verbose:
            print(
                "INFO ({}) .... read_fwf complete".format(
                    datetime.now().time().isoformat(timespec="milliseconds")
                )
            )
            print(
                "INFO ({}) .... Unpacking and validating fields ...".format(
                    datetime.now().time().isoformat(timespec="milliseconds")
                )
            )

        self.data = self.data.assign(value_check="")
        self.data = self.data.assign(code_check="")
        self.data = self.data.assign(bad_data=False)
        # apply scaling factors and validate
        self.data = self.validation(self.data)

        # add columns to store date and location
        self.data = self.data.assign(date=pd.NaT)
        self.data = self.data.assign(location="NULL")
        self.data = self.data.assign(icv=version)
        self.data = self.data.assign(record=self.record_index[self.idx])
        self.data = self.data.assign(
            idx=self.data["attm98.uid"].apply(lambda x: int(x, 36))
        )
        self.data["core.lon"] = self.data.apply(
            lambda x: to_180(x),
            axis=1,
        )
        # set location variable
        self.data["location"] = self.data.apply(
            lambda x: to_position_str(x),
            axis=1,
        )
        # set date variable
        # for early data, if hour missing set to local time
        testSeries = self.data.apply(
            lambda x: to_datetime_str(x),
            axis=1,
        )
        check = pv.validate_datetime(testSeries, return_type="mask_series")
        if any(check):
            self.data.loc[check, "value_check"] = (
                self.data.loc[check, "value_check"] + ":" + "date"
            )
            self.data.loc[check, "bad_data"] = True
            print("bad dates ...")
            print(testSeries[check].unique())

        self.data.loc[~check, "date"] = self.data[~check].apply(
            lambda x: to_datetime(x),
            axis=1,
        )
        return True
