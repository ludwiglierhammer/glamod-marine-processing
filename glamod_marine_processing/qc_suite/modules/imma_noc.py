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
                    self.conv[item["name"]] = imma_converters.get(
                        self.colTypes[item["name"]]
                    )

    def md5(self, fname):
        """Return MD5 hash."""
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

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
            for s1, s2 in zip(
                attmSentinals, list(map(lambda x: " " * (x - 4), attmLength))
            )
        ]
        attmLength = dict(zip(attmIndex, attmLength))

        if self.content_buffer is None:
            # read file into buffer
            try:
                if zipped:
                    with gzip.open(filename, "r", encoding="utf-8") as content_file:
                        content = content_file.read()
                else:
                    with open(filename, encoding="utf-8") as content_file:
                        content = content_file.read()
            except UnicodeDecodeError:
                print("Using cp1252 character set")
                if zipped:
                    with gzip.open(filename, "r", encoding="cp1252") as content_file:
                        content = content_file.read()
                else:
                    with open(filename, encoding="cp1252") as content_file:
                        content = content_file.read()
            except Exception:
                raise ("Error reading file: " + filename)
            self.content_buffer = pd.Series(list(io.StringIO(content)))
            if sort:
                sort_key = self.content_buffer.str.slice(
                    34, 43
                )  # callsign in columns 36 - 43
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

        if block_size is None:
            idx = list(range(self.number_records))
            self.cursor = self.number_records
        else:
            idx = list(
                range(self.cursor, min(self.cursor + block_size, self.number_records))
            )
            self.cursor = min(self.cursor + block_size, self.number_records)

        # following required for python 2
        # content = unicode( content, "utf-8")
        # content_buffer = pd.Series(list(io.StringIO(content)))
        # record_index = content_buffer.index.values

        tmpDict = dict(zip(self.record_index[idx], self.content_buffer[idx]))

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
        self.data = pd.read_fwf(
            read_buffer,
            widths=self.colWidths,
            header=None,
            names=self.colNames,
            converters=self.conv,
        )
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
        for column in self.data:
            if (
                (column != "value_check")
                & (column != "bad_data")
                & (column != "code_check")
            ):  # & \
                # (column != 'date') & (column != 'location' ):
                if (self.colTypes[column] == "float") & (
                    self.colScale[column] is not None
                ):
                    self.data[column] = self.data[column].apply(
                        lambda x: apply_scale(x, self.colScale[column], fmiss)
                    )
                if (
                    (self.colTypes[column] == "int")
                    | (self.colTypes[column] == "base36")
                    | (self.colTypes[column] == "float")
                ):
                    # print("Validating values : " + column)
                    testSeries = self.data[column]
                    testSeries = pd.to_numeric(testSeries)
                    # replace imiss with nans
                    testSeries = testSeries.replace(to_replace=imiss, value=fmiss)
                    check = pv.validate_numeric(
                        testSeries,
                        min_value=self.colMin[column],
                        max_value=self.colMax[column],
                        return_type="mask_series",
                    )
                    if any(check):
                        print(self.data.loc[check, column].unique())
                        self.data.loc[check, "value_check"] = (
                            self.data.loc[check, "value_check"] + ":" + column
                        )
                        self.data.loc[check, "bad_data"] = True
                if self.codetable[column] is not None:
                    # load code table
                    # print(  "Validating codes : " + self.codetable[ column ] )
                    valid_codes = pd.read_csv(self.codetable[column], sep="\t")
                    testSeries = self.data[column]
                    if (self.colTypes[column] == "int") | (
                        self.colTypes[column] == "base36"
                    ):
                        testSeries = testSeries.map(round).map(str)
                    white_list = valid_codes["code"]
                    white_list = white_list.map(str)
                    white_list = white_list.append(
                        pd.Series([str(imiss), cmiss, str(fmiss)])
                    )
                    check = pv.validate_string(
                        testSeries, whitelist=white_list, return_type="mask_series"
                    )
                    # check values either in code table or missing
                    if any(check):
                        print(self.data.loc[check, column].unique())
                        self.data.loc[check, "code_check"] = (
                            self.data.loc[check, "code_check"] + ":" + column
                        )
                        self.data.loc[check, "bad_data"] = True

        # add columns to store date and location
        self.data = self.data.assign(date=pd.NaT)
        self.data = self.data.assign(location="NULL")
        self.data = self.data.assign(icv=version)
        self.data = self.data.assign(record=self.record_index[idx])
        self.data = self.data.assign(
            idx=self.data["attm98.uid"].apply(lambda x: int(x, 36))
        )
        self.data["core.lon"] = self.data.apply(
            lambda x: x["core.lon"] - 360 if x["core.lon"] >= 180 else x["core.lon"],
            axis=1,
        )
        # set location variable
        self.data["location"] = self.data.apply(
            lambda x: "POINT("
            + str(round(x["core.lon"], 5))
            + " "
            + str(round(x["core.lat"], 5))
            + ")",
            axis=1,
        )
        # set date variable
        # for early data, if hour missing set to local time
        testSeries = self.data.apply(
            lambda x: str(x["core.yr"])
            + "-"
            + str(x["core.mo"])
            + "-"
            + str(x["core.dy"]),
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
            lambda x: datetime(
                year=x["core.yr"], month=x["core.mo"], day=x["core.dy"], hour=12
            )
            + relativedelta(hours=x["core.lon"] / 15)
            if pd.np.isnan(x["core.hr"])
            else datetime(
                year=x["core.yr"],
                month=x["core.mo"],
                day=x["core.dy"],
                hour=math.floor(x["core.hr"]),
                minute=round(60 * (x["core.hr"] - math.floor(x["core.hr"]))),
            ),
            axis=1,
        )
        # self.cksum = self.md5( filename )
        return True
