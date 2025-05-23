"""
Suite of functions to extend, work with and quality control IMMA data.
It includes classes to work with individual reports (class`.MarineReport`),
collections of reports (class`.Deck`) and class`.Voyage` objects composed
of observations from a single vessel (or observations with the same ID, which
is not always the same thing). These classes together with
class`.MarineReportQC` can be used to do Quality Control and Quality
Improvement on single reports and collections of reports.
"""

from __future__ import annotations

import math
from datetime import datetime

import numpy as np

from . import CalcHums, qc
from . import spherical_geometry as sph
from . import track_check as tc
from . import trackqc as tqc

VARLIST = [
    "YR",
    "MO",
    "DY",
    "HR",
    "LAT",
    "LON",
    "DS",
    "VS",
    "SLP",
    "AT",
    "AT2",
    "SST",
    "DCK",
    "PT",
    "SID",
    "DPT",
    "SHU",
    "VAP",
    "CRH",
    "CWB",
    "DPD",
    "W",
    "WI",
    "D",
    "DI",
    "WW",
]

# VARLIST = ['YR', 'MO', 'DY', 'HR', 'LAT', 'LON', 'DS', 'VS', 'ID', 'AT', 'SST',
#            'DPT',  'DCK', 'SLP',  'SID', 'PT', 'UID', 'W', 'D',  'IRF']


def safe_filename(infilename):
    """
    Take a filename and remove special characters like the asterisk and slash which mess things up. Warning: if you
    pass a directory path to this function, it will remove the slashes. Do not do that.

    :param infilename: filename to be processed.
    :type infilename: string
    :return: string with asterisk and slash replaced by underscores
    :rtype: string
    """
    safename = infilename.replace("/", "_")
    safename = safename.replace("*", "_")

    return safename


def datestring(year, month, day):
    """
    Write year month and day in iso format

    :param year: Year
    :param month: Month
    :param day: Day
    :type year: integer
    :type month: integer
    :type day:  integer

    :return: String containing ISO format year month day
    :rtype: string
    """
    syear = str(year)
    smonth = str(month)
    sday = str(day)
    try:
        outstr = (
            datetime.strptime(syear + " " + smonth + " " + sday, "%Y %m %d")
            .date()
            .isoformat()
        )
    except Exception:
        outstr = "0000-00-00"
    return outstr


def tostring(variable):
    r"""
    print a variable as string, or \\N if missing
    :type variable: float
    """
    if variable is not None:
        repout = str(variable)
    else:
        repout = "\\N"
    return repout


def pvar(var, mdi, scale):
    """
    Convert a variable to a rounded integer

    :param var: the variable to be scaled and rounded
    :param mdi: the value to set the variable to if missing or None
    :param scale: the factor by which to scale the number before rounding
    :type var: float
    :type mdi: integer
    :type scale: integer
    """
    if var is None:
        ret = mdi
    else:
        ret = round(var * scale)
    return ret


def get_threshold_multiplier(total_nobs, nob_limits, multiplier_values):
    """
    Find the highest value of i such that total_nobs is greater
    than nob_limits[i] and return multiplier_values[i]

    :param total_nobs: total number of neighbour observations
    :param nob_limits: list containing the limiting numbers of observations in
                       ascending order first element must be zero
    :param multiplier_values: list containing the multiplier values associated.
    :type total_nobs: integer
    :type nob_limits: List[integer]
    :type multiplier_values: List[float]
    :return: the multiplier value
    :rtype: float

    This routine is used by the buddy check. It's a bit niche.
    """
    assert len(nob_limits) == len(
        multiplier_values
    ), "length of input lists are different"
    assert min(multiplier_values) > 0, "multiplier value less than zero"
    assert min(nob_limits) == 0, "nob_limit of less than zero given"
    assert nob_limits[0] == 0, "lowest nob_limit not equal to zero"

    if len(nob_limits) > 1:
        for i in range(1, len(nob_limits)):
            assert (
                nob_limits[i] > nob_limits[i - 1]
            ), "nob_limits not in ascending order"

    multiplier = -1
    if total_nobs == 0:
        multiplier = 4.0

    for i in range(0, len(nob_limits)):
        if total_nobs > nob_limits[i]:
            multiplier = multiplier_values[i]

    assert multiplier > 0, "output multiplier less than or equal to zero "

    return multiplier


class MultivariableClimatology:
    """
    A class that can be used to hold and retrieve multiple climatology fields
    for a single variable. e.g. mean and standard deviation of SST. It could
    also be used to store background fields or some other reference data.
    """

    def __init__(self):
        self.statistic_dic = {}

    def add_statistic(self, statistic_name, climatology_field):
        """
        Add a particular climatology field representing a given statistic e.g. 'mean'

        :param statistic_name: the name of the statistic e.g. 'mean', 'stdev'
        :param climatology_field: the climatology field to be added
        :type statistic_name: string
        :type climatology_field: numpy array
        """
        self.statistic_dic[statistic_name] = climatology_field

    def get_statistic(self, statistic_name):
        """
        Get a particular climatology field representing a given statistic e.g. 'mean'

        :param statistic_name: the name of the statistic e.g. 'mean', 'stdev'
        :type statistic_name: string
        :return: climatology field corresponding to requested statistic name
        :rtype: numpy array
        """
        assert statistic_name in self.statistic_dic, "unknown climatology type"
        return self.statistic_dic[statistic_name]


class ClimatologyLibrary:
    """
    Class for holding collections of class`.MultivariableClimatology` and adding
    and getting fields from it.
    """

    def __init__(self):
        self.climlib = {}

    def add_field(self, variable_name, statistic_name, climatology_field):
        """
        Add a field representing a particular statistic (e.g. mean, stdev) for a
        particular variable (e.g. SST, AT).

        :param variable_name: Name of the variable that the field represents
        :param statistic_name: Name of the statistic that the field represents
        :param climatology_field: The field itself
        :type variable_name: string
        :type statistic_name: string
        :type climatology_field: numpy array
        """
        if variable_name in self.climlib:
            self.climlib[variable_name].add_statistic(statistic_name, climatology_field)
        else:
            tempc = MultivariableClimatology()
            tempc.add_statistic(statistic_name, climatology_field)
            self.climlib[variable_name] = tempc

    def get_field(self, variable_name, statistic_name):
        """
        Add a field representing a particular statistic (e.g. mean, stdev) for a
        particular variable (e.g. SST, AT).

        :param variable_name: Name of the variable that the field represents
        :param statistic_name: Name of the statistic that the field represents
        :type variable_name: string
        :type statistic_name: string
        :return: The field itself
        :rtype: numpy array
        """
        assert variable_name in self.climlib, "unnkown variable name: " + variable_name
        return self.climlib[variable_name].get_statistic(statistic_name)


class QC_filter:
    """A simple QC filter that can have specific tests added to it, which are then used to filter lists of MarineReports."""

    def __init__(self):
        self.filter = []

    def add_qc_filter(self, qc_type, specific_flag, qc_status):
        """
        Add a QC test to a QC filter

        :param qc_type: the general class of QC test e.g SST, AT, POS
        :param specific_flag: the name of the QC flag to be tested.
        :param qc_status: the value the specific_flag should have
        :type qc_type: string
        :type specific_flag: string
        :type qc_status: integer
        """
        self.filter.append([qc_type, specific_flag, qc_status])

    def test_report(self, rep):
        """
        Find out if a particular MarineReport passes the QC filter

        :param rep: the MarineReport to be tested
        :type rep: MarineReport
        :return: 0 for pass 1 for fail
        :rtype: integer
        """
        result = 0  # pass
        for filt in self.filter:
            if rep.get_qc(filt[0], filt[1]) != filt[2]:
                result = 1  # fail
        return result

    def split_reports(self, reps):
        """
        Split a list of MarineReports into those that pass and those that fail
        the QC filter.

        :param reps: the class`.Deck` of MarineReports to be filtered
        :type reps: Deck
        :return: two Decks of MarineReports, those that pass and those that fail
        :rtype: Deck

        This is not the most efficient way of doing things. It is now possible to
        add a class`.QC_filter` to a class`.Deck`, obviating the need to split
        and regroup the obs.
        """
        passes = Deck()
        fails = Deck()

        nobs = len(reps)

        for i in range(0, nobs):
            rep = reps.pop(0)

            if self.test_report(rep) == 0:
                passes.append(rep)
            else:
                fails.append(rep)

        return passes, fails


class ClimVariable:
    """
    A simple class for defining a climate variable which is an object with a climatological
    average and an optional standard deviation.
    """

    def __init__(self, clim, stdev=None):
        """
        Initialise a class`.ClimVariable`

        :param clim: climatological average
        :param stdev: climatological standard deviation
        :type clim: float
        :type stdev: float
        """
        if clim is None:
            self.clim = clim
        else:
            self.clim = float(clim)

        if stdev is None:
            self.stdev = stdev
        else:
            self.stdev = float(stdev)

    def getclim(self, intype="clim"):
        """
        Get the climatological value from the climate variable

        :param intype: which part of the ClimVariable do you want 'clim' or 'stdev', default is 'clim'
        :type intype: string
        """
        assert intype in ["clim", "stdev"], "unknown type " + str(intype)
        if intype == "stdev":
            return self.stdev
        elif intype == "clim":
            return self.clim

    def setclim(self, clim, intype="clim"):
        """
        Set the climatological value of the climate variable

        :param clim: climatological average
        :param intype: which part of the ClimVariable do you want to set 'clim' or 'stdev', default is 'clim'
        :type clim: float
        :type intype: string
        """
        assert intype in ["clim", "stdev"], "unknown type " + str(intype)
        if intype == "stdev":
            self.stdev = float(clim)
        elif intype == "clim":
            self.clim = float(clim)


class MarineReport:
    """
    A class for holding and working with marine reports. The core of the report is a set of data
    which are taken from an IMMA record used to initialise the class. The report also has an extendible
    set of QC flags, climate variables and a dictionary for adding new variables that might be needed.
    """

    def __init__(self, imma_rec):
        # ['YR','MO','DY','HR','LAT','LON','DS','VS','SLP','AT','SST','DCK','PT','SID','DPT']
        self.data = np.zeros(len(VARLIST))
        self.data += np.nan
        if "ID" in imma_rec.data:
            self.id = imma_rec.data["ID"]
            if self.id is None:
                self.id = ""
        else:
            self.id = ""
        if "UID" in imma_rec.data:
            self.uid = imma_rec.data["UID"]
        else:
            self.uid = None
        # dictionary copied element by element to reduce memory usage
        for k in imma_rec.data:
            if imma_rec.data[k] is not None and k in VARLIST:
                self.setvar(k, imma_rec.data[k])

        self.qc = {}
        self.climate_variables = {}
        self.ext = {}

        self.calculate_dt()
        self.calculate_dsi_vsi()

        self.special_qc_types = ["POS", "SST", "AT", "DPT", "SLP", "W", "D"]

    def lat(self):
        """Return latitude in range [-90,90]."""
        return self.getvar("LAT")

    def lon(self):
        """Return longitude in range [-180,180]."""
        outlon = self.getvar("LON")
        if outlon > 180:
            outlon -= 360.0
        return outlon

    def calculate_dsi_vsi(self):
        """Convert ICOADS DS and VS to meaningful units, in this case degrees and knots."""
        self.ext["dsi"] = None
        if self.getvar("DS") is not None:
            # print(self.getvar('DS'))
            # self.ext['dsi'] = ds_convert[self.getvar('DS')]
            self.ext["dsi"] = self.getvar("DS")

        self.ext["vsi"] = None
        if self.getvar("VS") is not None:
            if self.getvar("YR") >= 1968:
                self.ext["vsi"] = self.getvar("VS") * 5.0 - 2.0
            else:
                self.ext["vsi"] = self.getvar("VS") * 3.0 - 1.0
            if self.getvar("VS") == 0:
                self.ext["vsi"] = 0.0

    def calculate_humidity_variables(self, hum_vars):
        """
        The listed hum_vars have to be the five calculated humidity variables: 'SHU','VAP','CRH','CWB','DPD'
        There has to be an AT and DPT present to calculate any one of these/
        This also depends on there being a climatological SLP present
        This uses the CalcHums.py functions.

        :param hum_vars: list of humidity variables to calculate
        :type hum_vars: list of strings

        Note that the variables will all be set to None if the SLP climatology
        is not available
        """
        assert all(
            [i in ["SHU", "VAP", "CRH", "CWB", "DPD"] for i in hum_vars]
        ), "Not all hum vars are present: SHU,VAP,CRH,CWB,DPD"

        # Need climatological SLP for calculations
        slpclim = self.climate_variables["SLP"].getclim()
        if slpclim is None:
            for var in hum_vars:
                self.setvar(var, None)
        else:
            # Calculate the humidity variables
            self.setvar(
                "VAP", CalcHums.vap(self.getvar("DPT"), self.getvar("AT"), slpclim)
            )
            self.setvar(
                "SHU", CalcHums.sh(self.getvar("DPT"), self.getvar("AT"), slpclim)
            )
            self.setvar(
                "CRH", CalcHums.rh(self.getvar("DPT"), self.getvar("AT"), slpclim)
            )
            self.setvar(
                "CWB", CalcHums.wb(self.getvar("DPT"), self.getvar("AT"), slpclim)
            )
            self.setvar("DPD", CalcHums.dpd(self.getvar("DPT"), self.getvar("AT")))

            # Test for silliness - if silly, return all as None
            if self.getvar("CRH") is None:
                for var in hum_vars:
                    self.setvar(var, None)
            else:
                if (self.getvar("CRH") < 0.0) or (self.getvar("CRH") > 150.0):
                    for var in hum_vars:
                        self.setvar(var, None)

    def reset_ext(self):
        """Remove all extra data and recalculate the unpacked speeds and directions."""
        self.ext = {}
        self.calculate_dsi_vsi()

    def calculate_dt(self):
        """
        Used to set the internal julian day time in the marine report. This might need to be
        updated if any of the time variables are changed.
        """
        if self.getvar("YR") is not None:
            mlen = qc.get_month_lengths(self.getvar("YR"))
            if (
                self.getvar("MO") is not None
                and self.getvar("HR") is not None
                and self.getvar("DY") is not None
                and 0 < self.getvar("DY") <= mlen[self.getvar("MO") - 1]
            ):
                rounded_hour = int(math.floor(self.getvar("HR")))
                rounded_minute = int(
                    math.floor(60 * (self.getvar("HR") - rounded_hour))
                )
                self.dt = datetime(
                    self.getvar("YR"),
                    self.getvar("MO"),
                    int(self.getvar("DY")),
                    rounded_hour,
                    rounded_minute,
                )
            else:
                self.dt = None
        else:
            self.dt = None

    def __sub__(self, other):
        """
        Subtracting one class`.MarineReport` from another will yield the speed, distance, course and
        the time difference between the two reports.

        Usage: speed, distance, course, timediff = report_a - report_b
        """
        distance = sph.sphere_distance(self.lat(), self.lon(), other.lat(), other.lon())

        timediff = qc.time_difference(
            other.getvar("YR"),
            other.getvar("MO"),
            other.getvar("DY"),
            other.getvar("HR"),
            self.getvar("YR"),
            self.getvar("MO"),
            self.getvar("DY"),
            self.getvar("HR"),
        )
        if timediff != 0 and timediff is not None:
            speed = distance / timediff
        else:
            timediff = 0.0
            speed = distance

        course = sph.course_between_points(
            other.lat(), other.lon(), self.lat(), self.lon()
        )

        return speed, distance, course, timediff

    def __eq__(self, other):
        """Two marine reports are equal if their ID is equal and they were taken at the same time."""
        if self.getvar("ID") == other.getvar("ID") and self.dt == other.dt:
            return True
        else:
            return False

    def __gt__(self, other):
        """
        One marine report is greater than another if its ID is higher in an alphabetical ordering.
        For reports with the same ID, the later report is the greater.
        """
        if self.getvar("ID") > other.getvar("ID"):
            return True
        if (
            self.getvar("ID") == other.getvar("ID")
            and self.dt is not None
            and other.dt is not None
            and self.dt > other.dt
        ):
            return True
        else:
            return False

    def __ge__(self, other):
        """
        One marine report is greater than another if its ID is higher in an alphabetical ordering.
        For reports with the same ID, the later report is the greater.
        """
        if self.getvar("ID") > other.getvar("ID"):
            return True
        if self.getvar("ID") == other.getvar("ID") and self.dt >= other.dt:
            return True
        else:
            return False

    def __le__(self, other):
        """
        One marine report is greater than another if its ID is higher in an alphabetical ordering.
        For reports with the same ID, the later report is the greater.
        """
        if self.getvar("ID") < other.getvar("ID"):
            return True
        if self.getvar("ID") == other.getvar("ID") and self.dt <= other.dt:
            return True
        else:
            return False

    def add_climate_variable(self, name, clim, stdev=None):
        """
        Add a climate variable to a marine report

        :param name: the name of the climate variable
        :param clim: the climatological average of the climate variable
        :param stdev: optional standard deviation, default is None
        :type name: string
        :type clim: float
        :type stdev: float
        """
        self.climate_variables[name] = ClimVariable(clim, stdev)

    def getnorm(self, varname, intype="clim"):
        """
        Retrieve the climatological average for a particular climate variable

        :param varname: the name of the climate variable for which you want the climatological average
        :param intype: the type of norm required 'clim' for climatological average and 'stdev' for standard deviation,
            default is 'clim'
        :type varname: string
        :type intype: string
        :return: the climatological average (if the climate variable exists), None otherwise.
        :rtype: float
        """
        if varname in self.climate_variables:
            return self.climate_variables[varname].getclim(intype)
        else:
            return None

    def getanom(self, varname):
        """
        Retrieve the anomaly for a particular climate variable

        :param varname: the name of the climate variable for which you want the anomaly
        :type varname: string
        :return: the anomaly (if the climate variable exists), None otherwise.
        :rtype: float
        """
        if varname in self.climate_variables:
            clim = self.climate_variables[varname].getclim()
            if self.getvar(varname) is not None and clim is not None:
                return self.getvar(varname) - clim
            else:
                return None
        else:
            return None

    def get_normalised_anom(self, varname):
        """
        Retrieve the anomaly for a particular climate variable

        :param varname: the name of the climate variable for which you want the anomaly
        :type varname: string
        :return: the anomaly (if the climate variable exists) standardised by the standard deviation, None otherwise.
        :rtype: float
        """
        if varname in self.climate_variables:
            clim = self.climate_variables[varname].getclim()
            stdev = self.climate_variables[varname].getclim("stdev")
            if (
                self.getvar(varname) is not None
                and clim is not None
                and stdev is not None
            ):
                return (self.getvar(varname) - clim) / stdev
            else:
                return None
        else:
            return None

    def getext(self, varname):
        """
        Function to get a particular variable from the extended data

        :param varname: variable name to be retrieved from the extended data
        :type varname: string
        :return: the named variable
        :rtype: depends on the variable
        """
        assert varname in self.ext, "unknown extended variable name " + varname
        return self.ext[varname]

    def setext(self, varname, varvalue):
        """
        Set a particular variable in the extended data

        :param varvalue: value of variable to be set
        :param varname: variable name to be set in the extended data
        :type varvalue: float
        :type varname: string
        """
        self.ext[varname] = varvalue

    def setvar(self, varname, varvalue):
        """
        Set a particular variable in the data

        :param varvalue: value of variable to be set
        :param varname: variable name to be set in the extended data
        :type varvalue: float
        :type varname: string
        """
        if varname == "ID":
            self.id = varvalue
        elif varname == "UID":
            self.uid = varvalue
        else:
            i = VARLIST.index(varname)
            self.data[i] = varvalue

        if varname in ["YR", "DY", "HR"]:
            self.calculate_dt()

    def getvar(self, varname):
        """
        Get a variable which is either in the data or extended data. Both data and extended data
        will be queried and the function returns None if the varname is not found in either one.

        :param varname: variable name to be retrieved
        :type varname: string
        :return: the named variable from either the data or extended data
        :rtype: depends on the variable
        """
        if varname == "ID":
            return self.id
        if varname == "UID":
            return self.uid
        if not (varname in VARLIST or varname in self.ext):
            return None
        if varname in VARLIST:
            i = VARLIST.index(varname)
            if np.isnan(self.data[i]):
                return None
            if varname in ["YR", "MO", "DY", "DS", "VS", "DCK", "PT", "SID"]:
                return int(self.data[i])  # these are integer data types
            else:
                return self.data[i]
        else:
            return self.ext[varname]

    def set_qc(self, qc_type, specific_flag, set_value):
        """
        Set a particular QC flag

        :param qc_type: the general QC area e.g. SST, MAT. Must be either 'POS' or correspond to an ICOADS variable name
        :param specific_flag: the name of the flag to be set e.g. buddy_check, repeated_value
        :param set_value: the value which is to be given to the flag
        :type qc_type: string
        :type specific_flag: string
        :type set_value: integer in 0-9

        The specified flag in the general QC area of qc_type is set to the given value. This
        should be a reasonably flexible system to which new QC flags can be easily added.
        """
        assert set_value in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], "value not in 0-9" + str(
            set_value
        )
        assert (qc_type in self.special_qc_types) or (qc_type in VARLIST), (
            "unknown data type " + qc_type
        )

        self.qc[qc_type + specific_flag] = set_value

    def get_qc(self, qc_type, specific_flag):
        """
        Get the value of a particular QC flag

        :param qc_type: the general QC area e.g. SST, MAT..
        :param specific_flag: the name of the flag whose value is to be returned e.g. buddy_check, repeated_value
        :type qc_type: string
        :type specific_flag: string
        :return: the value of the flag, or 9 if the flag is not set.
        :rtype: integer

        Returns the value of a specific_flag or 9 if the specific_flag is not set.
        """
        if qc_type + specific_flag in self.qc:
            return self.qc[qc_type + specific_flag]
        else:
            return 9

    def saturated(self):
        """
        Quick check to see if the air is saturate
        i.e. Dew Point Temperature equals Air Temperature

        :return: True if the air is saturated, False otherwise
        :rtype: boolean
        """
        if (
            self.getvar("DPT") == self.getvar("AT")
            and self.getvar("AT") is not None
            and self.getvar("DPT") is not None
        ):
            return True
        else:
            return False

    def printvar(self, var):
        """Print a variable substituting -32768 for Nones."""
        if var in VARLIST:
            return int(pvar(self.getvar(var), -32768, 1.0))
        else:
            return int(pvar(-32768, -32768, 1.0))

    def printsim(self):
        """Print the WMO pub47 field"""
        if "SIM" in VARLIST:
            if self.getvar("SIM") is None:
                return "Missing"
            else:
                return self.getvar("SIM")
        else:
            return "None"

    def print_longform_report(self):
        """A simple routine to print out the marine report in old-fashioned fixed-width ascii style."""
        day = int(pvar(self.getvar("DY"), -32768, 1))
        hur = int(pvar(self.getvar("HR"), -32768, 100))

        mat = int(pvar(self.getvar("AT"), -32768, 10))
        matanom = int(pvar(self.getanom("AT"), -32768, 100))
        sst = int(pvar(self.getvar("SST"), -32768, 10))
        sstanom = int(pvar(self.getanom("SST"), -32768, 100))

        slp = int(pvar(self.getvar("SLP"), -32768, 10))
        # Added vars for humidity variables and anomalies
        # (anoms set to 0 for now until we sort out clims)

        dpt = int(pvar(self.getvar("DPT"), -32768, 10))
        dptanom = int(pvar(self.getanom("DPT"), -32768, 100))
        shu = int(pvar(self.getvar("SHU"), -32768, 10))
        shuanom = int(pvar(self.getanom("SHU"), -32768, 100))
        vap = int(pvar(self.getvar("VAP"), -32768, 10))
        vapanom = int(pvar(self.getanom("VAP"), -32768, 100))
        crh = int(pvar(self.getvar("CRH"), -32768, 10))
        crhanom = int(pvar(self.getanom("CRH"), -32768, 100))
        cwb = int(pvar(self.getvar("CWB"), -32768, 10))
        cwbanom = int(pvar(self.getanom("CWB"), -32768, 100))
        dpd = int(pvar(self.getvar("DPD"), -32768, 10))
        dpdanom = int(pvar(self.getanom("DPD"), -32768, 100))

        dsvs = 9999
        if self.getvar("DS") is not None and self.getvar("VS") is not None:
            dsvs = self.getvar("DS") * 100 + self.getvar("VS")

        lon = round(self.lon() * 100, 0)

        shipid = self.getvar("ID")
        if shipid is None:
            shipid = "         "

        qc_block = "{:d}{:d}{:d}{:d}{:d}{:d}{:d}{:d} "
        qc_long_block = "{:d}{:d}{:d}{:d}{:d}{:d}{:d}{:d}{:d} "
        qc_end = "{:d}{:d}{:d}{:d}{:d}{:d}{:d}{:d}\n"

        repout = f"{shipid:9.9} "
        repout = repout + "{:8.8}".format(self.getvar("UID"))
        repout = repout + f"{int(round(self.lat() * 100, 0)):8d}"
        repout = repout + f"{int(lon):8d}"
        repout = repout + "{:8d}".format(self.getvar("YR"))
        repout = repout + "{:8d}".format(self.getvar("MO"))
        repout = repout + f"{day:8d}"
        repout = repout + f"{hur:8d}"

        repout = repout + f"{mat:8d}"
        repout = repout + f"{matanom:8d}"
        repout = repout + f"{sst:8d}"
        repout = repout + f"{sstanom:8d}"

        repout = repout + f"{slp:8d}"
        # KW The humidity variables
        repout = repout + f"{dpt:8d}"
        repout = repout + f"{dptanom:8d}"
        repout = repout + f"{shu:8d}"
        repout = repout + f"{shuanom:8d}"
        repout = repout + f"{vap:8d}"
        repout = repout + f"{vapanom:8d}"
        repout = repout + f"{crh:8d}"
        repout = repout + f"{crhanom:8d}"
        repout = repout + f"{cwb:8d}"
        repout = repout + f"{cwbanom:8d}"
        repout = repout + f"{dpd:8d}"
        repout = repout + f"{dpdanom:8d}"

        repout = repout + f"{dsvs:8d}"

        repout = repout + "{:8d}".format(self.getvar("DCK"))
        repout = repout + "{:8d}".format(self.printvar("PT"))

        repout = repout + " "

        repout = repout + qc_block.format(
            self.get_qc("POS", "day"),
            self.get_qc("POS", "land"),
            self.get_qc("POS", "trk"),
            self.get_qc("POS", "date"),
            self.get_qc("POS", "time"),
            self.get_qc("POS", "pos"),
            self.get_qc("POS", "blklst"),
            self.get_qc("POS", "iquam_track"),
        )
        repout = repout + qc_block.format(
            self.get_qc("SST", "bud"),
            self.get_qc("SST", "clim"),
            self.get_qc("SST", "nonorm"),
            self.get_qc("SST", "freez"),
            self.get_qc("SST", "noval"),
            self.get_qc("SST", "spike"),
            self.get_qc("SST", "bbud"),
            self.get_qc("SST", "rep"),
        )
        repout = repout + qc_block.format(
            self.get_qc("AT", "bud"),
            self.get_qc("AT", "clim"),
            self.get_qc("AT", "nonorm"),
            9,
            self.get_qc("AT", "noval"),
            self.get_qc("AT", "nbud"),
            self.get_qc("AT", "bbud"),
            self.get_qc("AT", "rep"),
        )

        # KW Added a new block for DPT
        repout = repout + qc_long_block.format(
            self.get_qc("DPT", "bud"),
            self.get_qc("DPT", "clim"),
            self.get_qc("DPT", "nonorm"),
            self.get_qc("DPT", "ssat"),
            self.get_qc("DPT", "noval"),
            self.get_qc("DPT", "round"),
            self.get_qc("DPT", "bbud"),
            self.get_qc("DPT", "rep"),
            self.get_qc("DPT", "repsat"),
        )

        repout = repout + qc_end.format(
            self.get_qc("POS", "few"), self.get_qc("POS", "ntrk"), 9, 9, 9, 9, 9, 9
        )

        return repout

    def print_report(self):
        """A simple routine to print out the marine report in old-fashioned fixed-width ascii style."""
        day = int(pvar(self.getvar("DY"), -32768, 1))
        hur = int(pvar(self.getvar("HR"), -32768, 100))

        mat = int(pvar(self.getvar("AT"), -32768, 10))
        matanom = int(pvar(self.getanom("AT"), -32768, 100))
        sst = int(pvar(self.getvar("SST"), -32768, 10))
        sstanom = int(pvar(self.getanom("SST"), -32768, 100))

        dsvs = 9999
        if self.getvar("DS") is not None and self.getvar("VS") is not None:
            dsvs = self.getvar("DS") * 100 + self.getvar("VS")

        lon = round(self.lon() * 100, 0)

        shipid = self.getvar("ID")
        if shipid is None:
            shipid = "         "

        qc_block = "{:d}{:d}{:d}{:d}{:d}{:d}{:d}{:d} "
        qc_end = "{:d}{:d}{:d}{:d}{:d}{:d}{:d}{:d}\n"

        repout = f"{shipid:9.9} "
        repout = repout + "{:8.8}".format(self.getvar("UID"))
        repout = repout + "{:8d}".format(int(round(self.getvar("LAT") * 100, 0)))
        repout = repout + f"{int(lon):8d}"
        repout = repout + "{:8d}".format(self.getvar("YR"))
        repout = repout + "{:8d}".format(self.getvar("MO"))
        repout = repout + f"{day:8d}"
        repout = repout + f"{hur:8d}"

        repout = repout + f"{mat:8d}"
        repout = repout + f"{matanom:8d}"
        repout = repout + f"{sst:8d}"
        repout = repout + f"{sstanom:8d}"

        repout = repout + f"{dsvs:8d}"

        repout = repout + "{:8d}".format(self.getvar("DCK"))
        repout = repout + "{:8d}".format(self.printvar("PT"))

        repout = repout + " "

        repout = repout + qc_block.format(
            self.get_qc("POS", "day"),
            self.get_qc("POS", "land"),
            self.get_qc("POS", "trk"),
            self.get_qc("POS", "date"),
            self.get_qc("POS", "time"),
            self.get_qc("POS", "pos"),
            self.get_qc("POS", "blklst"),
            self.get_qc("POS", "dup"),
        )
        repout = repout + qc_block.format(
            self.get_qc("SST", "bud"),
            self.get_qc("SST", "clim"),
            self.get_qc("SST", "nonorm"),
            self.get_qc("SST", "freez"),
            self.get_qc("SST", "noval"),
            self.get_qc("SST", "nbud"),
            self.get_qc("SST", "bbud"),
            self.get_qc("SST", "rep"),
        )
        repout = repout + qc_block.format(
            self.get_qc("AT", "bud"),
            self.get_qc("AT", "clim"),
            self.get_qc("AT", "nonorm"),
            9,
            self.get_qc("AT", "noval"),
            self.get_qc("AT", "nbud"),
            self.get_qc("AT", "bbud"),
            self.get_qc("AT", "rep"),
        )
        repout = repout + qc_block.format(9, 9, 9, 9, 9, 9, 9, 9)
        repout = repout + qc_end.format(
            self.get_qc("POS", "few"), self.get_qc("POS", "ntrk"), 9, 9, 9, 9, 9, 9
        )

        return repout

    def print_variable_block(self, varnames, header=False, printuid=True):
        """
        Print a block of variables in a standard format

        :param varnames: name of the variables to be written out
        :param header: flag to indicate whether to print a header or not
        :param printuid: switch to toggle printinf of the UID for run-on lines
        :type varnames: list of strings
        :type header: boolean
        :type printuid: boolean

        :return: string containing comma separated QC block
        :rtype: string
        """
        if header:
            if printuid:
                repout = ["UID,DATE,PENTAD,"]
            else:
                repout = [""]

            for var in varnames:
                if len(var) > 1:
                    joinedvar = "_".join(var)
                else:
                    joinedvar = var[0]
                repout.append(joinedvar)
                repout.append(",")
        else:
            if printuid:
                repout = [self.getvar("UID")]
                repout.append(",")

                # ISO date time
                repout.append(
                    ""
                    + datestring(
                        self.getvar("YR"), self.getvar("MO"), self.getvar("DY")
                    )
                )
                repout.append(",")
                # pentad
                try:
                    p = qc.which_pentad(self.getvar("MO"), self.getvar("DY"))
                except Exception:
                    p = 0

                repout.append(str(p))
                repout.append(",")
            else:
                repout = [""]

            for var in varnames:
                if var[0] == "ID":
                    if self.getvar(var[0]) is None:
                        repout.append(tostring(self.getvar(var[0])))
                        repout.append(",")
                    else:
                        repout.append('"' + tostring(self.getvar(var[0])) + '"')
                        repout.append(",")
                else:
                    if len(var) > 1:
                        repout.append(tostring(self.getanom(var[0])))
                        repout.append(",")
                    else:
                        repout.append(tostring(self.getvar(var[0])))
                        repout.append(",")

        # trim trailing comma off string and add newline
        repout = repout[:-1]
        repout.append("\n")
        repout = "".join(repout)
        return repout

    def print_qc_block(self, blockname, varnames, header=False, printuid=True):
        """
        Print a QC block in a standard format

        :param blockname: name of the QC block that is being printed out
        :param varnames: name of the QC flags to be written out
        :param header: flag to indicate whether to print a header or not
        :param printuid: flag to toggle printing UID for run-on lines
        :type blockname: string
        :type varnames: list of strings
        :type header: boolean
        :type printuid: boolean

        :return: string containing comma separated QC block
        :rtype: string
        """
        if header:
            if printuid:
                repout = ["UID,"]
            else:
                repout = [""]

            for var in varnames:
                repout.append(var)
                repout.append(",")
        else:
            if printuid:
                repout = [self.getvar("UID")]
                repout.append(",")
            else:
                repout = [""]

            for var in varnames:
                repout.append(f"{self.get_qc(blockname, var):d}")
                repout.append(",")
        repout = repout[:-1]
        repout.append("\n")
        repout = "".join(repout)
        return repout


class MarineReportQC(MarineReport):
    """
    An extension of the class`.MarineReport` which adds methods for applying base QC
    and QI (Quality Improvement) to the reports.
    """

    def perform_base_qc(self, parameters):
        """Run all the base QC checks defined in the Class."""
        self.do_fix_missing_hour()

        self.is_buoy()
        self.is_ship()
        self.is_deck_780()

        self.do_position_check()
        self.do_date_check()
        self.do_time_check()
        self.do_blacklist()
        self.do_day_check(parameters["base"]["time_since_sun_above_horizon"])

        self.humidity_blacklist()
        self.mat_blacklist()
        self.wind_blacklist()

        self.do_base_sst_qc(parameters["SST"])
        self.do_base_mat_qc(parameters["AT"])
        self.do_base_dpt_qc(parameters["DPT"])
        self.do_base_slp_qc(parameters["SLP"])
        self.do_base_wind_qc(parameters["W"])

        # special check for silly values in all humidity-related variables
        # and set DPT hardlimit flag if necessary
        self.set_qc("DPT", "hardlimit", 0)
        for var in ["AT", "DPT", "SHU", "RH"]:
            if qc.hard_limit(self.getvar(var), parameters[var]["hard_limits"]) == 1:
                self.set_qc("DPT", "hardlimit", 1)

        self.do_kate_mat_qc(parameters["AT"])

    def perform_base_wind_qc(self, parameters):
        """
        Run all the base Wind Speed QC checks

        :param parameters:
        :return:
        """
        self.do_fix_missing_hour()

        self.is_buoy()
        self.is_ship()

        self.wind_blacklist()

        self.do_position_check()
        self.do_date_check()
        self.do_time_check()
        self.do_blacklist()

        self.do_base_wind_qc(parameters["W"])

    def perform_base_dat_qc(self, parameters):
        """Run all the base Day Marine Air Temperature QC checks."""
        self.do_fix_missing_hour()

        self.is_buoy()
        self.is_ship()

        self.mat_blacklist()

        self.do_position_check()
        self.do_date_check()
        self.do_time_check()
        self.do_blacklist()
        self.do_day_check(parameters["base"]["time_since_sun_above_horizon"])

        self.do_base_dat_qc(parameters["DAT"])

    def perform_base_slp_qc(self, parameters):
        """Run all the base Sea Level Pressure QC checks."""
        self.do_fix_missing_hour()

        self.is_buoy()
        self.is_ship()
        self.is_deck_780()

        self.do_position_check()
        self.do_date_check()
        self.do_time_check()
        self.do_blacklist()
        self.do_day_check(parameters["base"]["time_since_sun_above_horizon"])

        self.do_base_slp_qc(parameters["SLP"])

    def perform_base_sst_qc(self, parameters):
        """Run all the base Sea Surface Temperature QC checks."""
        self.do_fix_missing_hour()

        self.is_buoy()
        self.is_ship()
        self.is_deck_780()

        self.do_position_check()
        self.do_date_check()
        self.do_time_check()
        self.do_blacklist()
        self.do_day_check(parameters["base"]["time_since_sun_above_horizon"])

        self.do_base_sst_qc(parameters["SST"])

    def do_fix_deck201_zero_hour(self):
        """
        Deck 201 GMT midnights are assigned to the wrong day,
        see Carella, Kent, Berry 2015 Appendix A3
        Reports from deck 201 before 1899 taken at the GMT midnight
        were moved one day before the reported date.
        """
        if (
            self.getvar("DCK") == 201
            and self.getvar("YR") < 1899
            and self.getvar("HR") == 0
        ):
            #            self.shift_day(-1)
            pass

    def do_fix_missing_hour(self):
        """
        Deck 701 has a whole bunch of otherwise good obs with missing Hours.
        Set to 0000UTC and recalculate the ob time
        """
        if (
            self.getvar("DCK") == 701
            and self.getvar("YR") < 1860
            and self.getvar("HR") is None
        ):
            self.setvar("HR", 0)
            self.calculate_dt()

    def do_position_check(self):
        """Perform the positional QC check on the report."""
        self.set_qc(
            "POS", "pos", qc.position_check(self.getvar("LAT"), self.getvar("LON"))
        )

    def do_date_check(self):
        """Perform the date QC check on the report."""
        self.set_qc(
            "POS",
            "date",
            qc.date_check(self.getvar("YR"), self.getvar("MO"), self.getvar("DY")),
        )

    def do_time_check(self):
        """Perform the time QC check on the report."""
        self.set_qc("POS", "time", qc.time_check(self.getvar("HR")))

    def do_day_check(self, time_since_sun_above_horizon):
        """Set the day/night flag on the report."""
        if (
            self.get_qc("POS", "pos") == 0
            and self.get_qc("POS", "date") == 0
            and self.get_qc("POS", "time") == 0
        ):
            self.set_qc(
                "POS",
                "day",
                qc.day_test(
                    self.getvar("YR"),
                    self.getvar("MO"),
                    self.getvar("DY"),
                    self.getvar("HR"),
                    self.lat(),
                    self.lon(),
                    time_since_sun_above_horizon,
                ),
            )
        else:
            self.set_qc("POS", "day", 1)

    def do_blacklist(self):
        """Do basic blacklisting on the report."""
        self.set_qc(
            "POS",
            "blklst",
            qc.blacklist(
                self.getvar("ID"),
                self.getvar("DCK"),
                self.getvar("YR"),
                self.getvar("MO"),
                self.lat(),
                self.lon(),
                self.getvar("PT"),
            ),
        )

    def do_base_wind_qc(self, parameters):
        """Run the base Wind speed QC checks."""
        self.set_qc("W", "noval", qc.value_check(self.getvar("W")))
        self.set_qc(
            "W", "hardlimit", qc.hard_limit(self.getvar("W"), parameters["hard_limits"])
        )
        self.set_qc(
            "W",
            "consistency",
            qc.wind_consistency(
                self.getvar("W"), self.getvar("D"), parameters["variable_limit"]
            ),
        )

    def do_base_slp_qc(self, parameters):
        """Run the base SLP QC checks, non-missing, climatology check and check for normal."""
        assert "maximum_anomaly" in parameters
        self.set_qc("SLP", "noval", qc.value_check(self.getvar("SLP")))
        self.set_qc(
            "SLP",
            "clim",
            qc.climatology_plus_stdev_with_lowbar(
                self.getvar("SLP"),
                self.getnorm("SLP"),
                self.getnorm("SLP", "stdev"),
                parameters["maximum_standardised_anomaly"],
                parameters["lowbar"],
            ),
        )
        #        self.set_qc('SLP', 'clim', qc.climatology_check(self.getvar('SLP'), self.getnorm('SLP'),
        #                                                        parameters['maximum_anomaly']))
        self.set_qc("SLP", "nonorm", qc.no_normal_check(self.getnorm("SLP")))

    def do_base_sst_qc(self, parameters):
        """
        Run the base SST QC checks, non-missing, above freezing, climatology check
        and check for normal
        """
        assert "freezing_point" in parameters
        assert "freeze_check_n_sigma" in parameters
        assert "maximum_anomaly" in parameters

        self.set_qc("SST", "noval", qc.value_check(self.getvar("SST")))

        self.set_qc(
            "SST",
            "freez",
            qc.sst_freeze_check(
                self.getvar("SST"),
                0.0,
                parameters["freezing_point"],
                parameters["freeze_check_n_sigma"],
            ),
        )

        self.set_qc(
            "SST",
            "clim",
            qc.climatology_check(
                self.getvar("SST"), self.getnorm("SST"), parameters["maximum_anomaly"]
            ),
        )

        self.set_qc("SST", "nonorm", qc.no_normal_check(self.getnorm("SST")))
        self.set_qc(
            "SST",
            "hardlimit",
            qc.hard_limit(self.getvar("SST"), parameters["hard_limits"]),
        )

    def do_base_mat_qc(self, parameters):
        """Run the base MAT QC checks, non-missing, climatology check and check for normal etc."""
        assert "maximum_anomaly" in parameters

        self.set_qc("AT", "noval", qc.value_check(self.getvar("AT")))
        self.set_qc(
            "AT",
            "clim",
            qc.climatology_check(
                self.getvar("AT"), self.getnorm("AT"), parameters["maximum_anomaly"]
            ),
        )
        self.set_qc("AT", "nonorm", qc.no_normal_check(self.getnorm("AT")))
        self.set_qc(
            "AT",
            "hardlimit",
            qc.hard_limit(self.getvar("AT"), parameters["hard_limits"]),
        )

    def do_base_dat_qc(self, parameters):
        """Run the base DAT QC checks, non-missing, climatology check and check for normal etc."""
        assert "maximum_anomaly" in parameters

        self.set_qc("DAT", "noval", qc.value_check(self.getvar("DAT")))
        self.set_qc(
            "DAT",
            "clim",
            qc.climatology_check(
                self.getvar("DAT"), self.getnorm("DAT"), parameters["maximum_anomaly"]
            ),
        )
        self.set_qc("DAT", "nonorm", qc.no_normal_check(self.getnorm("DAT")))
        self.set_qc(
            "DAT",
            "hardlimit",
            qc.hard_limit(self.getvar("DAT"), parameters["hard_limits"]),
        )

    def do_kate_mat_qc(self, parameters):
        """
        Kate's modified MAT checks, non missing, modified climatology check, check for normal etc.
        Has a mix of AT and AT2 because we want to keep two sets of climatologies and checks for humidity
        """
        self.set_qc(
            "AT2",
            "clim",
            qc.climatology_plus_stdev_check(
                self.getvar("AT2"),
                self.getnorm("AT2"),
                self.getnorm("AT2", "stdev"),
                parameters["minmax_standard_deviation"],
                parameters["maximum_standardised_anomaly"],
            ),
        )

        self.set_qc("AT2", "noval", qc.value_check(self.getvar("AT2")))
        self.set_qc("AT2", "nonorm", qc.no_normal_check(self.getnorm("AT2")))
        self.set_qc(
            "AT2",
            "hardlimit",
            qc.hard_limit(self.getvar("AT"), parameters["hard_limits"]),
        )

    def do_base_dpt_qc(self, parameters):
        """
        Run the base DPT checks, non missing, modified climatology check, check for normal,
        supersaturation etc.
        """
        self.set_qc(
            "DPT",
            "clim",
            qc.climatology_plus_stdev_check(
                self.getvar("DPT"),
                self.getnorm("DPT"),
                self.getnorm("DPT", "stdev"),
                parameters["minmax_standard_deviation"],
                parameters["maximum_standardised_anomaly"],
            ),
        )

        self.set_qc("DPT", "noval", qc.value_check(self.getvar("DPT")))
        self.set_qc("DPT", "nonorm", qc.no_normal_check(self.getnorm("DPT")))
        self.set_qc(
            "DPT", "ssat", qc.supersat_check(self.getvar("DPT"), self.getvar("AT2"))
        )

    def is_deck_780(self):
        """Identify obs that are from ICOADS Deck 780 which consists of obs from WOD."""
        if self.getvar("DCK") == 780:
            self.set_qc("POS", "is780", 1)
        else:
            self.set_qc("POS", "is780", 0)

    def wind_blacklist(self):
        """Flag certain sources as ineligible for wind QC. Based on Shawn Smith's list."""
        self.set_qc("W", "wind_blacklist", 0)

        if self.getvar("DCK") in [708, 780]:
            self.set_qc("W", "wind_blacklist", 1)

        pass

    def humidity_blacklist(self):
        """Flag certain sources as ineligible for humidity QC."""
        self.set_qc("DPT", "hum_blacklist", 0)
        if self.getvar("PT") in [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 15]:
            self.set_qc("DPT", "hum_blacklist", 0)
        else:
            self.set_qc("DPT", "hum_blacklist", 1)

    def mat_blacklist(self):
        """
        Flag certain decks, areas and other sources as ineligible for MAT QC.
        These exclusions are based on Kent et al. HadNMAT2 paper and include
        Deck 780 which is oceanographic data and the North Atlantic, Suez,
        Indian Ocean area in the 19th Century.
        """
        # See Kent et al. HadNMAT2 QC section
        self.set_qc("AT", "mat_blacklist", 0)

        if self.getvar("PT") == 5 and self.getvar("DCK") == 780:
            self.set_qc("AT", "mat_blacklist", 1)

        # make sure lons are in range -180 to 180
        lon = self.lon()
        lat = self.lat()
        # North Atlantic, Suez and indian ocean to be excluded from MAT processing
        if (
            self.getvar("DCK") == 193
            and 1880 <= self.getvar("YR") <= 1892
            and (
                (-80.0 <= lon <= 0.0 and 40.0 <= lat <= 55.0)
                or (-10.0 <= lon <= 30.0 and 35.0 <= lat <= 45.0)
                or (15.0 <= lon <= 45.0 and -10.0 <= lat <= 40.0)
                or (15.0 <= lon <= 95.0 and lat >= -10.0 and lat <= 15.0)
                or (95.0 <= lon <= 105.0 and -10.0 <= lat <= 5.0)
            )
        ):
            self.set_qc("AT", "mat_blacklist", 1)

    def is_buoy(self):
        """
        Identify whether report is from a moored or drifting buoy based
        on ICOADS platform type PT. Set additional flag to pick out drifters only
        """
        if self.getvar("PT") in [6, 7]:
            self.set_qc("POS", "isbuoy", 1)
        else:
            self.set_qc("POS", "isbuoy", 0)

        if self.getvar("PT") == 7:
            self.set_qc("POS", "isdrifter", 1)
        else:
            self.set_qc("POS", "isdrifter", 0)

    def is_ship(self):
        """
        Identify whether report is from a ship based
        on ICOADS platform type PT
        """
        if self.getvar("PT") in [0, 1, 2, 3, 4, 5, 10, 11, 12, 17]:
            self.set_qc("POS", "isship", 1)
        else:
            self.set_qc("POS", "isship", 0)


class Voyage:
    """
    Class for handling lists of MarineReports as coherent sets of measurements
    from a single ship. Includes track check and repeated value checks which
    operate on all the observations in the class`.Voyage`.
    """

    def __init__(self):
        self.reps = []

    def __len__(self):
        """Return length."""
        return len(self.reps)

    def rep_feed(self):
        """Function for iterating over the MarineReports in a Voyage."""
        yield from self.reps

    def getrep(self, position):
        """
        Get the report for a particular location in the list

        :param position: the position the desired report occupies in the list
        :type position: integer
        :return: MarineReport at required index in the Voyage
        :rtype: MarineReport
        """
        return self.reps[position]

    def last_rep(self):
        """
        Get the last report in the Voyage

        :return: last MarineReport in the Voyage
        :rtype: MarineReport
        """
        nreps = len(self.reps)
        return self.reps[nreps - 1]

    def setvar(self, position, varname, value):
        """
        Set a particular variable from a particular report

        :param position: the position the desired report occupies in the list
        :param varname: the variable name to recover
        :param value: the variable value
        :type position: integer
        :type varname: string
        :type value: float or string
        """
        return self.reps[position].setvar(varname, value)

    def getvar(self, position, varname):
        """
        Get a particular variable from a particular report

        :param position: the position the desired report occupies in the list
        :param varname: the variable name to recover
        :type position: integer
        :type varname: string
        :return: variable value at required index
        :rtype: string, float
        """
        return self.reps[position].getvar(varname)

    def set_qc(self, position, qc_type, specific_flag, set_value):
        """
        Set the QC flag of a report at a specified position to a specified value

        :param position: the position the desired report occupies in the list
        :param qc_type: the general QC area e.g. SST, MAT...
        :param specific_flag: the name of the flag to be set e.g. buddy_check, repeated_value
        :param set_value: the value which is to be given to the flag
        :type position: integer
        :type qc_type: string
        :type specific_flag: string
        :type set_value: integer in 0-9
        """
        self.reps[position].set_qc(qc_type, specific_flag, set_value)

    def get_qc(self, position, qc_type, specific_flag):
        """
        Get the QC flag for a report at a specified position

        :param position: the position the desired report occupies in the list
        :param qc_type: the general QC area e.g. SST, MAT...
        :param specific_flag: the name of the flag to be set e.g. buddy_check, repeated_value
        :type position: integer
        :type qc_type: string
        :type specific_flag: string
        :return: the value which is to be given to the flag
        :rtype set_value: integer in 0-9
        """
        return self.reps[position].get_qc(qc_type, specific_flag)

    def add_report(self, rep):
        """
        Add a MarineReport to the Voyage.

        :param rep: MarineReport to be added to the end of the Voyage
        :type rep: MareineReport
        """
        self.reps.append(rep)

        if len(self.reps) > 1:
            i = len(self.reps)
            shpspd, shpdis, shpdir, tdiff = self.reps[i - 1] - self.reps[i - 2]
            self.reps[i - 1].setext("speed", shpspd)
            self.reps[i - 1].setext("course", shpdir)
            self.reps[i - 1].setext("distance", shpdis)
            self.reps[i - 1].setext("time_diff", tdiff)
        else:
            self.reps[0].setext("speed", None)
            self.reps[0].setext("course", None)
            self.reps[0].setext("distance", None)
            self.reps[0].setext("time_diff", None)

    def sort(self):
        """Sorts the reports into time order."""
        self.reps.sort()
        # then recalculate times, speeds etc.
        if len(self.reps) > 1:
            for i in range(1, len(self.reps)):
                shpspd, shpdis, shpdir, tdiff = self.reps[i] - self.reps[i - 1]
                self.reps[i].setext("speed", shpspd)
                self.reps[i].setext("course", shpdir)
                self.reps[i].setext("distance", shpdis)
                self.reps[i].setext("time_diff", tdiff)

    def get_speed(self):
        """
        Return a list containing the speeds of all the reports as
        estimated from the positions of consecutive reports

        :return: list of speeds in km/hr
        :rtype: list[float]
        """
        spd = []
        for i in range(0, len(self.reps)):
            spd.append(self.reps[i].getext("speed"))

        return spd

    def meansp(self):
        """
        Calculate the mean speed of the voyage based on speeds
        estimated from the positions of consecutive reports.

        :return: mean voyage speed
        :rtype: float
        """
        spd = self.get_speed()

        if len(spd) > 1:
            amean = np.mean(spd[1:])
        else:
            amean = None

        return amean

    def calc_alternate_speeds(self):
        """The speeds and courses can also be calculated using alternating reports."""
        for i in range(0, len(self.reps)):
            self.reps[i].setext("alt_speed", None)
            self.reps[i].setext("alt_course", None)
            self.reps[i].setext("alt_distance", None)
            self.reps[i].setext("alt_time_diff", None)

        if len(self.reps) > 2:
            for i in range(1, len(self.reps) - 1):
                shpspd, shpdis, shpdir, tdiff = self.reps[i + 1] - self.reps[i - 1]
                self.reps[i].setext("alt_speed", shpspd)
                self.reps[i].setext("alt_course", shpdir)
                self.reps[i].setext("alt_distance", shpdis)
                self.reps[i].setext("alt_time_diff", tdiff)

    def find_saturated_runs(self, parameters):
        """
        Perform checks on persistence of 100% rh while going through the voyage.
        While going through the voyage repeated strings of 100 %rh (AT == DPT) are noted.
        If a string extends beyond 20 reports and two days/48 hrs in time then all values are set to
        fail the repsat qc flag.
        """
        min_time_threshold = parameters["min_time_threshold"]
        shortest_run = parameters["shortest_run"]

        satcount = []

        for i, rep in enumerate(self.reps):
            self.reps[i].set_qc("DPT", "repsat", 0)

            if rep.saturated():
                satcount.append(i)

            elif not (rep.saturated()) and len(satcount) > shortest_run:
                shpspd, shpdis, shpdir, tdiff = (
                    self.reps[satcount[len(satcount) - 1]] - self.reps[satcount[0]]
                )

                if tdiff >= min_time_threshold:
                    for loc in satcount:
                        self.reps[loc].set_qc("DPT", "repsat", 1)
                    satcount = []
                else:
                    satcount = []

            else:
                satcount = []

        if len(satcount) > shortest_run:
            shpspd, shpdis, shpdir, tdiff = (
                self.reps[satcount[len(satcount) - 1]] - self.reps[satcount[0]]
            )
            del shpspd
            del shpdis
            del shpdir

            if tdiff >= min_time_threshold:
                for loc in satcount:
                    self.reps[loc].set_qc("DPT", "repsat", 1)

        return

    def find_multiple_rounded_values(self, parameters, intype="DPT"):
        """
        Find instances when more than "threshold" of the observations are
        whole numbers and set the 'round' flag. Used in the humidity QC
        where there are times when the values are rounded and this may
        have caused a bias.

        :param parameters: A dictionary with two entries 'threshold' Fraction of obs in a class`.Voyage` above which
            rounded obs are flagged and 'min_count' the smallest number of observations to which this check can be applied
        :param intype: variable name being checked 'DPT' is default
        :type intype: string
        """
        assert intype in ["SST", "AT", "AT2", "DPT"]

        min_count = parameters["min_count"]
        threshold = parameters["threshold"]

        assert 0.0 <= threshold <= 1.0

        # initialise
        for rep in self.reps:
            rep.set_qc(intype, "round", 0)

        valcount = {}
        allcount = 0

        for i, rep in enumerate(self.reps):
            if rep.getvar(intype) is not None:
                allcount += 1
                if str(rep.getvar(intype)) in valcount:
                    valcount[str(rep.getvar(intype))].append(i)
                else:
                    valcount[str(rep.getvar(intype))] = [i]

        if allcount > min_count:
            wholenums = 0
            for key in valcount:
                if float(key).is_integer():
                    wholenums = wholenums + len(valcount[key])

            if float(wholenums) / float(allcount) >= threshold:
                for key in valcount:
                    if float(key).is_integer():
                        for i in valcount[key]:
                            self.reps[i].set_qc(intype, "round", 1)

        return

    def find_repeated_values(self, parameters, intype="SST"):
        """
        Find cases where more than a given proportion of SSTs have the same value

        :param parameters: a dictionary with two entries, 'threshold' the maximum fraction of observations that can
            have a given value and 'min_count' the smallest sequence of observations that this check will be performed
            on
        :param intype: either 'SST' or 'MAT' to find repeated SSTs or MATs
        :type intype: string

        This method goes through a voyage and finds any cases where more than a threshold fraction of
        the observations have the same SST or NMAT values or whatever.
        """
        assert intype in ["SST", "AT", "AT2", "DPT", "SLP"]

        threshold = parameters["threshold"]
        assert 0.0 <= threshold <= 1.0

        min_count = parameters["min_count"]

        # initialise
        for rep in self.reps:
            rep.set_qc(intype, "rep", 0)

        valcount = {}
        allcount = 0

        for i, rep in enumerate(self.reps):
            if rep.getvar(intype) is not None:
                allcount += 1
                if str(rep.getvar(intype)) in valcount:
                    valcount[str(rep.getvar(intype))].append(i)
                else:
                    valcount[str(rep.getvar(intype))] = [i]

        if allcount > min_count:
            for key in valcount:
                if float(len(valcount[key])) / float(allcount) > threshold:
                    for i in valcount[key]:
                        self.reps[i].set_qc(intype, "rep", 1)
                else:
                    for i in valcount[key]:
                        self.reps[i].set_qc(intype, "rep", 0)

        return

    def predict_next_point(self, timediff):
        """
        The latitude and longitude of the next point are estimated based on
        an extrapolation of the great circle drawn between the previous two
        points

        :param timediff: predict the latitude and longitude after this timediff has elapsed.
        :type timediff: float
        """
        assert timediff >= 0
        nreps = len(self.reps)

        assert nreps > 0, "Need at least one report in the voyage to predict"

        if nreps == 1:
            return self.reps[0].lat(), self.reps[0].lon()

        if abs(self.reps[nreps - 1].getvar("time_diff")) < 0.00001:
            return (self.reps[nreps - 1].lat(), self.reps[nreps - 1].lon())

        # take last-but-one and last point. Calculate a speed and
        # great circle course from them.
        course = self.reps[nreps - 1].getvar("course")
        distance = self.reps[nreps - 1].getvar("speed") * (
            self.reps[nreps - 1].getvar("time_diff") + timediff
        )

        lat1 = self.reps[nreps - 2].lat()
        lon1 = self.reps[nreps - 2].lon()

        lat, lon = sph.lat_lon_from_course_and_distance(lat1, lon1, course, distance)

        return lat, lon

    def distr1(self):
        """
        calculate what the distance is between the projected position (based on the reported
        speed and heading at the current and previous time steps) and the actual position. The
        observations are taken in time order.

        :return: list of distances from estimated positions
        :rtype: list of floats

        This takes the speed and direction reported by the ship and projects it forwards half a
        time step, it then projects it forwards another half time step using the speed and
        direction for the next report, to which the projected location
        is then compared. The distances between the projected and actual locations is returned
        """
        km_to_nm = 0.539957

        nobs = len(self)

        distance_from_est_location = [None]

        for i in range(1, nobs):
            if (
                self.getvar(i, "vsi") is not None
                and self.getvar(i - 1, "vsi") is not None
                and self.getvar(i, "dsi") is not None
                and self.getvar(i - 1, "dsi") is not None
                and self.getvar(i, "time_diff") is not None
            ):
                # get increment from initial position
                lat1, lon1 = tc.increment_position(
                    self.getvar(i - 1, "LAT"),
                    self.getvar(i - 1, "LON"),
                    self.getvar(i - 1, "vsi") / km_to_nm,
                    self.getvar(i - 1, "dsi"),
                    self.getvar(i, "time_diff"),
                )

                lat2, lon2 = tc.increment_position(
                    self.getvar(i, "LAT"),
                    self.getvar(i, "LON"),
                    self.getvar(i, "vsi") / km_to_nm,
                    self.getvar(i, "dsi"),
                    self.getvar(i, "time_diff"),
                )
                # apply increments to the lat and lon at i-1
                alatx = self.getvar(i - 1, "LAT") + lat1 + lat2
                alonx = self.getvar(i - 1, "LON") + lon1 + lon2

                # calculate distance between calculated position and the second reported position
                discrepancy = sph.sphere_distance(
                    self.getvar(i, "LAT"), self.getvar(i, "LON"), alatx, alonx
                )

                distance_from_est_location.append(discrepancy)

            else:
                # in the absence of reported speed and direction set to None
                distance_from_est_location.append(None)

        return distance_from_est_location

    def distr2(self):
        """
        calculate what the
        distance is between the projected position (based on the reported speed and
        heading at the current and
        previous time steps) and the actual position. The calculation proceeds from the
        final, later observation to the
        first (in contrast to distr1 which runs in time order)

        :return: list of distances from estimated positions
        :rtype: list of floats

        This takes the speed and direction reported by the ship and projects it forwards half a time step, it then
        projects it forwards another half time step using the speed and direction for the next report, to which the
        projected location is then compared. The distances between the projected and actual locations is returned
        """
        km_to_nm = 0.539957

        nobs = len(self)

        distance_from_est_location = [None]

        for i in range(nobs - 1, 0, -1):
            if (
                self.getvar(i, "vsi") is not None
                and self.getvar(i - 1, "vsi") is not None
                and self.getvar(i, "dsi") is not None
                and self.getvar(i - 1, "dsi") is not None
                and self.getvar(i, "time_diff") is not None
            ):
                # get increment from initial position - backwards in time
                # means reversing the direction by 180 degrees
                lat1, lon1 = tc.increment_position(
                    self.getvar(i, "LAT"),
                    self.getvar(i, "LON"),
                    self.getvar(i, "vsi") / km_to_nm,
                    self.getvar(i, "dsi") - 180.0,
                    self.getvar(i, "time_diff"),
                )

                lat2, lon2 = tc.increment_position(
                    self.getvar(i - 1, "LAT"),
                    self.getvar(i - 1, "LON"),
                    self.getvar(i - 1, "vsi") / km_to_nm,
                    self.getvar(i - 1, "dsi") - 180.0,
                    self.getvar(i, "time_diff"),
                )

                # apply increments to the lat and lon at i-1
                alatx = self.getvar(i, "LAT") + lat1 + lat2
                alonx = self.getvar(i, "LON") + lon1 + lon2

                # calculate distance between calculated position and the second reported position
                discrepancy = sph.sphere_distance(
                    self.getvar(i - 1, "LAT"), self.getvar(i - 1, "LON"), alatx, alonx
                )
                distance_from_est_location.append(discrepancy)

            else:
                # in the absence of reported speed and direction set to None
                distance_from_est_location.append(None)

        # that fancy bit at the end reverses the array
        return distance_from_est_location[::-1]

    def midpt(self):
        """
        interpolate between alternate reports and compare the
        interpolated location to the actual location. e.g. take difference between
        reports 2 and 4 and interpolate to get an estimate for the position at the time
        of report 3. Then compare the estimated and actual positions at the time of
        report 3.

        :return: list of distances from estimated positions in km
        :rtype: list of floats

        The calculation linearly interpolates the latitudes and longitudes (allowing for
        wrapping around the dateline and so on).
        """
        nobs = len(self)

        midpoint_discrepancies = [None]

        for i in range(1, nobs - 1):
            t0 = self.getvar(i, "time_diff")
            t1 = self.getvar(i + 1, "time_diff")

            if t0 is not None and t1 is not None:
                if t0 + t1 != 0:
                    fraction_of_time_diff = t0 / (t0 + t1)
                else:
                    fraction_of_time_diff = 0.0
            else:
                fraction_of_time_diff = 0.0

            if fraction_of_time_diff > 1.0:
                print(fraction_of_time_diff, t0, t1)

            estimated_lat_at_midpt, estimated_lon_at_midpt = sph.intermediate_point(
                self.getvar(i - 1, "LAT"),
                self.getvar(i - 1, "LON"),
                self.getvar(i + 1, "LAT"),
                self.getvar(i + 1, "LON"),
                fraction_of_time_diff,
            )

            discrepancy = sph.sphere_distance(
                self.getvar(i, "LAT"),
                self.getvar(i, "LON"),
                estimated_lat_at_midpt,
                estimated_lon_at_midpt,
            )

            midpoint_discrepancies.append(discrepancy)

        midpoint_discrepancies.append(None)

        return midpoint_discrepancies

    def iquam_track_check(self, parameters):
        """
        Perform the IQUAM track check as detailed in Xu and Ignatov 2013

        The track check calculates speeds between pairs of observations and
        counts how many exceed a threshold speed. The ob with the most
        violations of this limit is flagged as bad and removed from the
        calculation. Then the next worst is found and removed until no
        violatios remain.
        """
        buoy_speed_limit = parameters["buoy_speed_limit"]  # 15.0 #km/h
        ship_speed_limit = parameters["ship_speed_limit"]  # 60.0 #km/h

        delta_d = parameters["delta_d"]  # 1.11 #0.1 degrees of latitude
        delta_t = parameters["delta_t"]  # 0.01 #one hundredth of an hour

        n_neighbours = parameters["number_of_neighbours"]

        numobs = len(self)

        if numobs == 0:
            return

        if qc.id_is_generic(self.getvar(0, "ID"), self.getvar(0, "YR")):
            for i in range(0, numobs):
                self.set_qc(i, "POS", "iquam_track", 0)
            return

        if self.getvar(0, "PT") in [6, 7]:
            speed_limit = buoy_speed_limit
        else:
            speed_limit = ship_speed_limit

        speed_violations = []
        count_speed_violations = []

        for t1 in range(0, numobs):
            self.set_qc(t1, "POS", "iquam_track", 0)

            violations_for_this_report = []
            count_violations_this_report = 0.0

            lo = max(0, t1 - n_neighbours)
            hi = min(numobs, t1 + n_neighbours + 1)

            for t2 in range(lo, hi):
                speed, distance, direction, time_diff = self.reps[t2] - self.reps[t1]
                del speed
                del direction

                iquam_condition = max([abs(distance) - delta_d, 0.0]) / (
                    abs(time_diff) + delta_t
                )

                if iquam_condition > speed_limit:
                    violations_for_this_report.append(t2)
                    count_violations_this_report += 1.0

            speed_violations.append(violations_for_this_report)
            count_speed_violations.append(count_violations_this_report)

        count = 0
        while np.sum(count_speed_violations) > 0.0:
            most_fails = np.argmax(count_speed_violations)
            self.set_qc(most_fails, "POS", "iquam_track", 1)

            for index in speed_violations[most_fails]:
                if most_fails in speed_violations[index]:
                    speed_violations[index].remove(most_fails)
                    count_speed_violations[index] -= 1.0

            count_speed_violations[most_fails] = 0
            count += 1

        return

    def track_check(self, parameters):
        """
        Perform one pass of the track check

        This is an implementation of the MDS track check code
        which was originally written in the 1990s. I don't know why this piece of
        historic trivia so exercises my mind, but it does: the 1990s! I wish my code
        would last so long.
        """
        max_direction_change = parameters["max_direction_change"]
        max_speed_change = parameters["max_speed_change"]
        max_absolute_speed = parameters["max_absolute_speed"]
        max_midpoint_discrepancy = parameters["max_midpoint_discrepancy"]

        km_to_nm = 0.539957
        nobs = len(self)

        # no obs in, no qc outcomes out
        if nobs == 0:
            return

        # Generic ids and buoys get a free pass on the track check
        if (
            qc.id_is_generic(self.getvar(0, "ID"), self.getvar(0, "YR"))
            or self.getvar(0, "PT") == 6
            or self.getvar(0, "PT") == 7
        ):
            nobs = len(self)
            for i in range(0, nobs):
                self.set_qc(i, "POS", "trk", 0)
                self.set_qc(i, "POS", "few", 0)
            return

        # fewer than three obs - set the fewsome flag
        # deck 720 gets a pass prior to 1891 see
        # Carella, Kent, Berry 2015 Appendix A3
        if nobs < 3:
            if self.getvar(0, "DCK") == 720 and self.getvar(0, "YR") < 1891:
                nobs = len(self)
                for i in range(0, nobs):
                    self.set_qc(i, "POS", "trk", 0)
                    self.set_qc(i, "POS", "few", 0)
                return
            else:
                nobs = len(self)
                for i in range(0, nobs):
                    self.set_qc(i, "POS", "trk", 0)
                    self.set_qc(i, "POS", "few", 1)
                return

        # work out speeds and distances between alternating points
        self.calc_alternate_speeds()
        # what are the mean and mode speeds?
        modal_speed = tc.modesp(self.get_speed())
        # set speed limits based on modal speed
        amax, amaxx, amin = tc.set_speed_limits(modal_speed)
        del amaxx
        del amin

        # compare reported speeds and positions if we have them
        forward_diff_from_estimated = self.distr1()
        reverse_diff_from_estimated = self.distr2()
        try:
            midpoint_diff_from_estimated = self.midpt()
        except Exception:
            print(self.getvar(0, "ID"))
            assert False

        # do QC
        self.set_qc(0, "POS", "trk", 0)
        self.set_qc(0, "POS", "few", 0)

        for i in range(1, nobs - 1):
            thisqc_a = 0
            thisqc_b = 0

            # together these cover the speeds calculate from point i
            if (
                self.getvar(i, "speed") is not None
                and self.getvar(i, "speed") > amax
                and self.getvar(i - 1, "alt_speed") is not None
                and self.getvar(i - 1, "alt_speed") > amax
            ):
                thisqc_a += 1.00
            elif (
                self.getvar(i + 1, "speed") is not None
                and self.getvar(i + 1, "speed") > amax
                and self.getvar(i + 1, "alt_speed") is not None
                and self.getvar(i + 1, "alt_speed") > amax
            ):
                thisqc_a += 2.00
            elif (
                self.getvar(i, "speed") is not None
                and self.getvar(i, "speed") > amax
                and self.getvar(i + 1, "speed") is not None
                and self.getvar(i + 1, "speed") > amax
            ):
                thisqc_a += 3.00

                # Quality-control by examining the distance
            # between the calculated and reported second position.
            thisqc_b += tc.check_distance_from_estimate(
                self.getvar(i, "vsi"),
                self.getvar(i - 1, "vsi"),
                self.getvar(i, "time_diff"),
                forward_diff_from_estimated[i],
                reverse_diff_from_estimated[i],
            )
            # Check for continuity of direction
            thisqc_b += tc.direction_continuity(
                self.getvar(i, "dsi"),
                self.getvar(i - 1, "dsi"),
                self.getvar(i, "course"),
                max_direction_change,
            )
            # Check for continuity of speed.
            thisqc_b += tc.speed_continuity(
                self.getvar(i, "vsi"),
                self.getvar(i - 1, "vsi"),
                self.getvar(i, "speed"),
                max_speed_change,
            )

            # check for speeds in excess of 40.00 knots
            if self.getvar(i, "speed") > max_absolute_speed / km_to_nm:
                thisqc_b += 10.0

            # make the final decision
            if (
                midpoint_diff_from_estimated[i] > max_midpoint_discrepancy / km_to_nm
                and thisqc_a > 0
                and thisqc_b > 0
            ):
                self.set_qc(i, "POS", "trk", 1)
                self.set_qc(i, "POS", "few", 0)
            else:
                self.set_qc(i, "POS", "trk", 0)
                self.set_qc(i, "POS", "few", 0)

        self.set_qc(nobs - 1, "POS", "trk", 0)
        self.set_qc(nobs - 1, "POS", "few", 0)

    def spike_check(self, parameters, intype="SST"):
        """
        Perform IQUAM like spike check on the class`.Voyage`.

        :param parameters: Parameter dictionary containing entries for max_gradient_space, max_gradient_time,
            ship_delta_t, buoy_delta_t and number_of_neighbours.
        :param intype: Variable to spike check (currently limited to SST)
        :type parameters: dictionary
        :type intype: string
        """
        numobs = len(self)

        if numobs == 0:
            return

        max_gradient_space = parameters["max_gradient_space"]  # K/km
        max_gradient_time = parameters["max_gradient_time"]  # K/hr

        ship_delta_t = parameters["ship_delta_t"]  # K
        buoy_delta_t = parameters["buoy_delta_t"]  # K

        n_neighbours = parameters["number_of_neighbours"]

        if self.getvar(0, "PT") in [6, 7]:
            delta_t = buoy_delta_t
        else:
            delta_t = ship_delta_t

        gradient_violations = []
        count_gradient_violations = []

        for t1 in range(0, numobs):
            self.set_qc(t1, intype, "spike", 0)

            violations_for_this_report = []
            count_violations_this_report = 0.0

            lo = max(0, t1 - n_neighbours)
            hi = min(numobs, t1 + n_neighbours + 1)

            for t2 in range(lo, hi):
                if (
                    self.getvar(t2, intype) is not None
                    and self.getvar(t1, intype) is not None
                ):
                    speed, distance, direction, time_diff = (
                        self.reps[t2] - self.reps[t1]
                    )
                    del speed
                    del direction
                    val_change = abs(self.getvar(t2, intype) - self.getvar(t1, intype))

                    iquam_condition = max(
                        [
                            delta_t,
                            abs(distance) * max_gradient_space,
                            abs(time_diff) * max_gradient_time,
                        ]
                    )

                    if val_change > iquam_condition:
                        violations_for_this_report.append(t2)
                        count_violations_this_report += 1.0

            gradient_violations.append(violations_for_this_report)
            count_gradient_violations.append(count_violations_this_report)

        count = 0
        while np.sum(count_gradient_violations) > 0.0:
            most_fails = np.argmax(count_gradient_violations)
            self.set_qc(most_fails, intype, "spike", 1)

            for index in gradient_violations[most_fails]:
                if most_fails in gradient_violations[index]:
                    gradient_violations[index].remove(most_fails)
                    count_gradient_violations[index] -= 1.0

            count_gradient_violations[most_fails] = 0
            count += 1

        return

    def buoy_aground_check(self, parameters, sort=True):
        """
        Perform drifting buoy tracking qc aground check on a class`.Voyage`.

        :param parameters: Parameter dictionary containing entries for smooth_win, min_win_period and max_win_period.
        :param sort: True to sort voyage reports in time before QC
        :type parameters: dictionary
        :type sort: boolean
        """
        numobs = len(self)
        if numobs == 0:
            print("no obs for qc, skipping aground check")
            return
        if self.getvar(0, "PT") != 7:
            print("voyage is not a drifter, skipping aground check")
            return
        if sort:
            self.sort()
        try:
            tqc.aground_check(
                self.reps,
                parameters["smooth_win"],
                parameters["min_win_period"],
                parameters["max_win_period"],
            )
        except AssertionError as error:
            raise AssertionError("buoy aground check failed to run: " + str(error))
        return

    def new_buoy_aground_check(self, parameters, sort=True):
        """
        Perform drifting buoy tracking qc aground check on a class`.Voyage`.

        :param parameters: Parameter dictionary containing entries for smooth_win and min_win_period.
        :param sort: True to sort voyage reports in time before QC
        :type parameters: dictionary
        :type sort: boolean
        """
        numobs = len(self)
        if numobs == 0:
            print("no obs for qc, skipping aground check")
            return
        if self.getvar(0, "PT") != 7:
            print("voyage is not a drifter, skipping aground check")
            return
        if sort:
            self.sort()
        try:
            tqc.new_aground_check(
                self.reps, parameters["smooth_win"], parameters["min_win_period"]
            )
        except AssertionError as error:
            raise AssertionError("buoy aground check failed to run: " + str(error))
        return

    def buoy_speed_check(self, parameters, sort=True):
        """
        Perform drifting buoy tracking qc speed check on a class`.Voyage`.

        :param parameters: Parameter dictionary containing entries for speed_limit, min_win_period and max_win_period.
        :param sort: True to sort voyage reports in time before QC
        :type parameters: dictionary
        :type sort: boolean
        """
        numobs = len(self)
        if numobs == 0:
            print("no obs for qc, skipping speed check")
            return
        if self.getvar(0, "PT") != 7:
            print("voyage is not a drifter, skipping speed check")
            return
        if sort:
            self.sort()
        try:
            tqc.speed_check(
                self.reps,
                parameters["speed_limit"],
                parameters["min_win_period"],
                parameters["max_win_period"],
            )
        except AssertionError as error:
            raise AssertionError("buoy speed check failed to run: " + str(error))
        return

    def new_buoy_speed_check(self, iquam_parameters, parameters, sort=True):
        """
        Perform drifting buoy tracking qc speed check on a class`.Voyage`.

        :param iquam_parameters: Parameter dictionary for Voyage.iquam_track_check() function.
        :param parameters: Parameter dictionary containing entries for speed_limit and min_win_period.
        :param sort: True to sort voyage reports in time before QC
        :type iquam_parameters: dictionary
        :type parameters: dictionary
        :type sort: boolean
        """
        numobs = len(self)
        if numobs == 0:
            print("no obs for qc, skipping speed check")
            return
        if self.getvar(0, "PT") != 7:
            print("voyage is not a drifter, skipping speed check")
            return
        if sort:
            self.sort()
        try:
            tqc.new_speed_check(
                self.reps,
                iquam_parameters,
                parameters["speed_limit"],
                parameters["min_win_period"],
            )
        except AssertionError as error:
            raise AssertionError("buoy speed check failed to run: " + str(error))
        return

    def buoy_tail_check(self, parameters, sort=True):
        """
        Perform drifting buoy tracking qc tail check on a class`.Voyage`.

        :param parameters: Parameter dictionary containing entries for long_win_len, long_err_std_n, short_win_len,
                           short_err_std_n, short_win_n_bad, drift_inter, drif_intra and background_err_lim.
        :param sort: True to sort voyage reports in time before QC
        :type parameters: dictionary
        :type sort: boolean
        """
        numobs = len(self)
        if numobs == 0:
            print("no obs for qc, skipping tail check")
            return
        if self.getvar(0, "PT") != 7:
            print("voyage is not a drifter, skipping tail check")
            return
        if sort:
            self.sort()
        try:
            tqc.sst_tail_check(
                self.reps,
                parameters["long_win_len"],
                parameters["long_err_std_n"],
                parameters["short_win_len"],
                parameters["short_err_std_n"],
                parameters["short_win_n_bad"],
                parameters["drift_inter"],
                parameters["drif_intra"],
                parameters["background_err_lim"],
            )
        except AssertionError as error:
            raise AssertionError("buoy tail check failed to run: " + str(error))
        return

    def buoy_bias_noise_check(self, parameters, sort=True):
        """
        Perform check for biased or noisy drifting buoys on a class`.Voyage`.

        :param parameters: Parameter dictionary containing entries for n_eval, bias_lim, drif_intra, drif_inter,
                           err_std_n, n_bad and background_err_lim.
        :param sort: True to sort voyage reports in time before QC
        :type parameters: dictionary
        :type sort: boolean
        """
        numobs = len(self)
        if numobs == 0:
            print("no obs for qc, skipping bias-noise check")
            return
        if self.getvar(0, "PT") != 7:
            print("voyage is not a drifter, skipping bias-noise check")
            return
        if sort:
            self.sort()
        try:
            tqc.sst_biased_noisy_check(
                self.reps,
                parameters["n_eval"],
                parameters["bias_lim"],
                parameters["drif_intra"],
                parameters["drif_inter"],
                parameters["err_std_n"],
                parameters["n_bad"],
                parameters["background_err_lim"],
            )
        except AssertionError as error:
            raise AssertionError("buoy bias-noise check failed to run: " + str(error))
        return

    def write_qc(self, runid, icoads_dir, year, month, allvarnames):
        """
        Write out QC flags for specified variable names from
        the contents of the class`.Deck`.
        """
        count_write = 0
        syr = str(year)
        smn = f"{month:02}"
        for var in allvarnames:
            outfilename = (
                var
                + "_qc_"
                + syr
                + smn
                + "_"
                + self.reps[0].getvar("ID")
                + "_"
                + runid
                + ".csv"
            )
            outfile = open(icoads_dir + "/" + outfilename, "w")
            outfile.write(
                self.reps[0].print_qc_block(var, allvarnames[var], header=True)
            )
            count_write = 0
            for rep in self.reps:
                if rep.getvar("YR") == year and rep.getvar("MO") == month:
                    outfile.write(
                        rep.print_qc_block(var, allvarnames[var], header=False)
                    )
                    count_write += 1
            outfile.close()

        print(f"wrote out {count_write} obs")
        return

    def write_tracking_output(self, runid, icoads_dir, year2, month2):
        """
        Write out the contents of the class`.Voyage` including variables and QC flags and tracking QC flags
        all in one file

        :param runid: a general name for this run to be added to the filename
        :param icoads_dir: directory into which the outputs get written
        :param year2: year of last observation in the voyage
        :param month2: month to last observation in the voyage
        :return: None
        """
        syr = str(year2)
        smn = f"{month2:02d}"

        safeid = safe_filename(self.reps[0].getvar("ID"))

        outfilename = "Tracking_" + syr + smn + "_" + safeid + "_" + runid + ".csv"
        outfile = open(icoads_dir + "/" + outfilename, "w")

        varnames = [["ID"], ["LON"], ["LAT"], ["YR"], ["MO"], ["DY"], ["HR"]]
        varnames2 = [["SST"], ["OSTIA"], ["BGVAR"], ["ICE"]]

        qc_block1 = [
            "day",
            "isship",
            "trk",
            "date",
            "time",
            "pos",
            "blklst",
            "isbuoy",
            "iquam_track",
            "isdrifter",
        ]  # POS
        qc_block2 = [
            "bud",
            "clim",
            "nonorm",
            "freez",
            "noval",
            "nbud",
            "bbud",
            "rep",
            "spike",
            "hardlimit",
        ]  # SST
        qc_block3 = ["drf_agr", "drf_spd"]  # tracking positional QC
        qc_block4 = [
            "drf_tail1",
            "drf_tail2",
            "drf_bias",
            "drf_noise",
            "drf_short",
        ]  # tracking other QC

        # UID, ID, LON, LAT, YR, MO, DY, HR, MDS QC flags, track QC flags, SST, OSTIA-SST, OSTIA-BGVAR, OSTIA-ICE.
        header1 = self.reps[0].print_variable_block(varnames, header=True)
        header2 = self.reps[0].print_qc_block(
            "POS", qc_block1, header=True, printuid=False
        )
        header3 = self.reps[0].print_qc_block(
            "SST", qc_block2, header=True, printuid=False
        )
        header4 = self.reps[0].print_qc_block(
            "POS", qc_block3, header=True, printuid=False
        )
        header5 = self.reps[0].print_qc_block(
            "SST", qc_block4, header=True, printuid=False
        )
        header6 = self.reps[0].print_variable_block(
            varnames2, header=True, printuid=False
        )

        outfile.write(
            header1.rstrip()
            + ","
            + header2.rstrip()
            + ","
            + header3.rstrip()
            + ","
            + header4.rstrip()
            + ","
            + header5.rstrip()
            + ","
            + header6
        )

        for rep in self.reps:
            vars1 = rep.print_variable_block(varnames)
            vars2 = rep.print_qc_block("POS", qc_block1, printuid=False)
            vars3 = rep.print_qc_block("SST", qc_block2, printuid=False)
            vars4 = rep.print_qc_block("POS", qc_block3, printuid=False)
            vars5 = rep.print_qc_block("SST", qc_block4, printuid=False)
            vars6 = rep.print_variable_block(varnames2, printuid=False)

            outfile.write(
                vars1.rstrip()
                + ","
                + vars2.rstrip()
                + ","
                + vars3.rstrip()
                + ","
                + vars4.rstrip()
                + ","
                + vars5.rstrip()
                + ","
                + vars6
            )

        outfile.close()

    def write_output(self, runid, icoads_dir, year, month):
        """Write out the contents of the class`.Voyage`."""
        count_write = 0
        syr = str(year)
        smn = f"{month:02}"

        safeid = safe_filename(self.reps[0].getvar("ID"))

        outfilename = "Variables_" + syr + smn + "_" + safeid + "_" + runid + ".csv"
        outfile = open(icoads_dir + "/" + outfilename, "w")
        varnames = [
            ["ID"],
            ["YR"],
            ["MO"],
            ["DY"],
            ["HR"],
            ["LAT"],
            ["LON"],
            ["AT"],
            ["AT", "anom"],
            ["SST"],
            ["SST", "anom"],
            ["DPT"],
            ["DPT", "anom"],
            ["SLP"],
            ["SLP", "anom"],
            ["OSTIA"],
            ["ICE"],
            ["BGVAR"],
        ]
        outfile.write(self.reps[0].print_variable_block(varnames, header=True))
        for rep in self.reps:
            if rep.getvar("YR") == year and rep.getvar("MO") == month:
                outfile.write(rep.print_variable_block(varnames))
                count_write += 1
        outfile.close()

        # write out base QC
        allvarnames = {
            "POS": [
                "day",
                "isship",
                "trk",
                "date",
                "time",
                "pos",
                "blklst",
                "isbuoy",
                "iquam_track",
                "isdrifter",
            ],
            "SST": [
                "bud",
                "clim",
                "nonorm",
                "freez",
                "noval",
                "nbud",
                "bbud",
                "rep",
                "spike",
                "hardlimit",
            ],
        }

        self.write_qc(runid, icoads_dir, year, month, allvarnames)

        print("wrote out ", count_write, " obs for", self.reps[0].getvar("ID"))

        return


class Np_Super_Ob:
    """Class for gridding data in buddy check, based on numpy arrays."""

    def __init__(self):
        self.grid = np.zeros((360, 180, 73))
        self.buddy_mean = np.zeros((360, 180, 73))
        self.buddy_stdev = np.zeros((360, 180, 73))
        self.nobs = np.zeros((360, 180, 73))

    def add_rep(self, lat, lon, year, month, day, anom):
        """Add an anomaly to the grid from specified lat lon and date."""
        xindex = qc.mds_lon_to_xindex(lon)
        yindex = qc.mds_lat_to_yindex(lat)
        pindex = qc.which_pentad(month, day) - 1

        assert 0 <= xindex < 360, "bad lon" + str(lon)
        assert 0 <= yindex < 180, "bad lat" + str(lat)
        assert 0 <= pindex < 73, "bad pentad" + str(month) + str(day)

        if anom is not None:
            self.grid[xindex][yindex][pindex] += anom
            self.nobs[xindex][yindex][pindex] += 1

    def take_average(self):
        """Take the average of a grid."""
        nonmiss = np.nonzero(self.nobs)
        self.grid[nonmiss] = self.grid[nonmiss] / self.nobs[nonmiss]

    def get_neighbour_anomalies(self, search_radius, xindex, yindex, pindex):
        """
        Search within a specified search radius of the given point and extract
        the neighbours for buddy check

        :param search_radius: three element array search radius in which to look lon, lat, time
        :param xindex: the xindex of the gridcell to start from
        :param yindex: the yindex of the gridcell to start from
        :param pindex: the pindex of the gridcell to start from
        :return: anomalies and numbers of observations in two lists
        :rtype: list of floats
        """
        assert len(search_radius) == 3, str(len(search_radius))

        radcon = 3.1415928 / 180.0

        latitude_approx = 89.5 - yindex

        xspan = search_radius[0]
        full_xspan = int(xspan / math.cos(latitude_approx * radcon))
        yspan = search_radius[1]
        pspan = search_radius[2]

        temp_anom = []
        temp_nobs = []

        for xpt in range(-1 * full_xspan, full_xspan + 1):
            for ypt in range(-1 * yspan, yspan + 1):
                for ppt in range(-1 * pspan, pspan + 1):
                    if xpt == 0 and ypt == 0 and ppt == 0:
                        continue

                    thisxx = (xindex + xpt) % 360
                    thisyy = (yindex + ypt) % 180
                    thispp = (pindex + ppt) % 73

                    if self.nobs[thisxx][thisyy][thispp] != 0:
                        temp_anom.append(self.grid[thisxx][thisyy][thispp])
                        temp_nobs.append(self.nobs[thisxx][thisyy][thispp])

        return temp_anom, temp_nobs

    def get_buddy_limits_with_parameters(
        self, pentad_stdev, limits, number_of_obs_thresholds, multipliers
    ):
        """Get buddy limits with parameters."""
        nonmiss = np.nonzero(self.nobs)
        for i in range(len(nonmiss[0])):
            xindex = nonmiss[0][i]
            yindex = nonmiss[1][i]
            pindex = nonmiss[2][i]
            m, d = qc.pentad_to_month_day(pindex + 1)

            stdev = pentad_stdev.get_value_mds_style(
                89.5 - yindex, -179.5 + xindex, m, d
            )

            if stdev is None or stdev < 0.0:
                stdev = 1.0

            match_not_found = True

            for j, limit in enumerate(limits):
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    limits[j], xindex, yindex, pindex
                )

                if len(temp_anom) > 0 and match_not_found:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(
                            total_nobs, number_of_obs_thresholds[j], multipliers[j]
                        )
                        * stdev
                    )

                    match_not_found = False

            if match_not_found:
                self.buddy_mean[xindex][yindex][pindex] = 0.0
                self.buddy_stdev[xindex][yindex][pindex] = 500.0

        return

    def get_buddy_limits(self, pentad_stdev):
        """Get buddy limits for old style buddy check."""
        nonmiss = np.nonzero(self.nobs)
        for i in range(len(nonmiss[0])):
            xindex = nonmiss[0][i]
            yindex = nonmiss[1][i]
            pindex = nonmiss[2][i]
            month, day = qc.pentad_to_month_day(pindex + 1)

            # bug noted here single field getsst but multiple fields passed
            stdev = pentad_stdev.get_value_mds_style(
                89.5 - yindex, -179.5 + xindex, month, day
            )

            if stdev is None or stdev < 0.0:
                stdev = 1.0

            match_not_found = True

            # if there is neighbour in that range then calculate a mean
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [1, 1, 2], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(
                            total_nobs, [0, 5, 15, 100], [4.0, 3.5, 3.0, 2.5]
                        )
                        * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # otherwise move out further in space and time to 2 degrees and 2 pentads
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [2, 2, 2], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(total_nobs, [0], [4.0]) * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # otherwise move out further in space and time to 2 degrees and 2 pentads
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [1, 1, 4], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(
                            total_nobs, [0, 5, 15, 100], [4.0, 3.5, 3.0, 2.5]
                        )
                        * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # final step out is to 2 degrees and 4 pentads
            if match_not_found:
                temp_anom, temp_nobs = self.get_neighbour_anomalies(
                    [2, 2, 4], xindex, yindex, pindex
                )

                if len(temp_anom) > 0:
                    self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)
                    total_nobs = np.sum(temp_nobs)

                    self.buddy_stdev[xindex][yindex][pindex] = (
                        get_threshold_multiplier(total_nobs, [0], [4.0]) * stdev
                    )

                    match_not_found = False
                    assert total_nobs != 0, "total number of obs is zero"

            # if there are no neighbours then any observation will get a pass
            if match_not_found:
                self.buddy_mean[xindex][yindex][pindex] = 0.0
                self.buddy_stdev[xindex][yindex][pindex] = 500.0

        return

    def get_new_buddy_limits(
        self, stdev1, stdev2, stdev3, limits=[2, 2, 4], sigma_m=1.0, noise_scaling=3.0
    ):
        """
        Get buddy limits for new bayesian buddy check

        :param stdev1: Field of standard deviations representing standard deviation of difference between target
            gridcell and complete neighbour average (grid area to neighbourhood difference)
        :param stdev2: Field of standard deviations representing standard deviation of difference between a single
            observation and the target gridcell average (point to grid area difference)
        :param stdev3: Field of standard deviations representing standard deviation of difference between random
            neighbour gridcell and full neighbour average (uncertainty in neighbour average)
        :param limits: three membered list of number of degrees in latitude and longitude and number of pentads
        :param sigma_m: Estimated measurement error uncertainty
        :param noise_scaling: scale noise by a factor of noise_scaling used to match observed variability
        :type stdev1: numpy array
        :type stdev2: numpy array
        :type stdev3: numpy array
        :type limits: list of floats
        :type sigma_m: float
        """
        nonmiss = np.nonzero(self.nobs)

        for i in range(len(nonmiss[0])):
            xindex = nonmiss[0][i]
            yindex = nonmiss[1][i]
            pindex = nonmiss[2][i]

            m, d = qc.pentad_to_month_day(pindex + 1)

            stdev1_ex = stdev1.get_value(89.5 - yindex, -179.5 + xindex, m, d)
            stdev2_ex = stdev2.get_value(89.5 - yindex, -179.5 + xindex, m, d)
            stdev3_ex = stdev3.get_value(89.5 - yindex, -179.5 + xindex, m, d)

            if stdev1_ex is None or stdev1_ex < 0.0:
                stdev1_ex = 1.0
            if stdev2_ex is None or stdev2_ex < 0.0:
                stdev2_ex = 1.0
            if stdev3_ex is None or stdev3_ex < 0.0:
                stdev3_ex = 1.0

            # if there is neighbour in that range then calculate a mean
            temp_anom, temp_nobs = self.get_neighbour_anomalies(
                limits, xindex, yindex, pindex
            )

            if len(temp_anom) > 0:
                self.buddy_mean[xindex][yindex][pindex] = np.mean(temp_anom)

                tot = 0.0
                ntot = 0.0
                for n_obs in temp_nobs:
                    # measurement error for each 1x1x5day cell
                    tot += sigma_m**2.0 / n_obs
                    # sampling error for each 1x1x5day cell
                    # multiply by three to match observed stdev
                    tot += noise_scaling * (stdev2_ex**2.0 / n_obs)
                    ntot += 1.0

                sigma_buddy = tot / (ntot**2.0)
                sigma_buddy += stdev3_ex**2.0 / ntot

                self.buddy_stdev[xindex][yindex][pindex] = math.sqrt(
                    sigma_m**2.0
                    + stdev1_ex**2.0
                    + noise_scaling * stdev2_ex**2.0
                    + sigma_buddy
                )

            else:
                self.buddy_mean[xindex][yindex][pindex] = 0.0
                self.buddy_stdev[xindex][yindex][pindex] = 500.0

        return

    def get_buddy_mean(self, lat, lon, month, day):
        """
        Get the buddy mean from the grid for a specified time and place

        :param lat: latitude of the location for which the buddy mean is desired
        :param lon: longitude of the location for which the buddy mean is desired
        :param month: month for which the buddy mean is desired
        :param day: day for which the buddy mean is desired
        :type lat: float
        :type lon: float
        :type month: integer
        :type day: integer
        """
        xindex = qc.mds_lon_to_xindex(lon)
        yindex = qc.mds_lat_to_yindex(lat)
        pindex = qc.which_pentad(month, day) - 1
        return self.buddy_mean[xindex][yindex][pindex]

    def get_buddy_stdev(self, lat, lon, month, day):
        """
        Get the buddy standard deviation from the grid for a specified time and place

        :param lat: latitude of the location for which the buddy standard deviation is desired
        :param lon: longitude of the location for which the buddy standard deviatio is desired
        :param month: month for which the buddy standard deviatio is desired
        :param day: day for which the buddy standard deviatio is desired
        :type lat: float
        :type lon: float
        :type month: integer
        :type day: integer
        """
        xindex = qc.mds_lon_to_xindex(lon)
        yindex = qc.mds_lat_to_yindex(lat)
        pindex = qc.which_pentad(month, day) - 1
        return self.buddy_stdev[xindex][yindex][pindex]


class Deck:
    """
    A class for aggregating individual MarineReports and doing things to them. For example,
    buddy checking them or extracting individual ship class`.Voyage`.It's called a class`.Deck`
    because that is the terminology used by ICOADS - literally a 'deck' of punched cards each
    containing one or more reports.

    There is no particular order imposed on the individual class`.MarineReport` objects, but
    they can be indexed and extracted by ID. A class`.QC_filter` can be added to the
    class`.Deck` which will then be used to decide which observations will be affected by
    subsequent Deck-level quality-control checks or methods.

    It's called a class`.Deck` because that is the terminology used by ICOADS - literally a
    'deck' of punched cards each containing one or more reports.
    """

    def __init__(self):
        self.reps = []
        self.idtracker = {}
        self.filter = QC_filter()

    def __len__(self):
        """Get length."""
        return len(self.reps)

    def append(self, rep):
        """
        Add a class`.MarineReport` to the class`.Deck`

        :param rep: class`.MarineReport` to be added to the class`.Deck`
        :type rep: class`.MarineReport`

        This function adds a marine report to the deck and updates the
        internal index of ships.
        """
        self.reps.append(rep)
        i = len(self) - 1
        if rep.getvar("ID") in self.idtracker:
            self.idtracker[rep.getvar("ID")].append(i)
        else:
            self.idtracker[rep.getvar("ID")] = [i]

    def sort(self):
        """
        Sort the MarineReports into ID-then-time order. This can be very slow
        for large numbers of observations.
        """
        self.reps.sort()
        self.index_by_id()

    def index_by_id(self):
        """
        Build an index of where obs from each ship are. This is then used by the method
        get_one_platform_at_a_time to yield a bunch of objects of class class`.Voyage`
        corresponding to all obs from a single ID.
        """
        for i, rep in enumerate(self.reps):
            if rep.getvar("ID") in self.idtracker:
                self.idtracker[rep.getvar("ID")].append(i)
            else:
                self.idtracker[rep.getvar("ID")] = [i]

    def pop(self, pos=0):
        """
        Pop a single MarineReport from the class`.Deck`

        :param pos: position in the deck of the observation to be popped.
        :type pos: integer
        """
        return self.reps.pop(pos)

    def set_qc(self, qc_type, specific_flag, set_value):
        """
        Set the QC state for all MarineReports in the class`.Deck`

        :param qc_type: the general QC area e.g. SST, MAT...
        :param specific_flag: the name of the flag to be set e.g. buddy_check, repeated_value
        :param set_value: the value which is to be given to the flag
        :type qc_type: string
        :type specific_flag: string
        :type set_value: integer in 0-9

        The specified flag in the general QC area of qc_type is set to the given value. This
        should be a reasonably flexible system to which new QC flags can be easily added.
        """
        for rep in self.reps:
            rep.set_qc(qc_type, specific_flag, set_value)
        return

    def add_filter(self, infilter):
        """
        Add a QC_filter to the Deck. This will be used to decide which observations will
        be affected by subsequent checks, such as the buddy check.

        :param infilter: class`.QC_filter` to be added to the Deck
        :type infilter: class`.QC_filter`
        """
        self.filter = infilter

    def mds_buddy_check(self, intype, pentad_stdev, parameters):
        """
        Do the old style buddy check. Only those observations that pass the QC_filter
        of the class will be buddy checked.

        :param intype: The variable name for the variable that is to be buddy checked.
        :param pentad_stdev: Field of standard deviations of 1x1xpentad standard deviations
        :param parameters: list of parameters for the buddy check
        :type intype: string
        :type pentad_stdev: numpy array
        """
        assert intype in ["SST", "AT", "DPT", "SLP"], intype

        limits = parameters["limits"]
        number_of_obs_thresholds = parameters["number_of_obs_thresholds"]
        multipliers = parameters["multipliers"]

        # calculate superob averages and numbers of observations
        grid = Np_Super_Ob()
        for rep in self.reps:
            if self.filter.test_report(rep) == 0:
                grid.add_rep(
                    rep.lat(),
                    rep.lon(),
                    rep.getvar("YR"),
                    rep.getvar("MO"),
                    rep.getvar("DY"),
                    rep.getanom(intype),
                )

        grid.take_average()
        grid.get_buddy_limits_with_parameters(
            pentad_stdev, limits, number_of_obs_thresholds, multipliers
        )

        # finally loop over all reports and update buddy QC
        for this_report in self.reps:
            if self.filter.test_report(this_report) == 0:
                lat = this_report.lat()
                lon = this_report.lon()
                mon = this_report.getvar("MO")
                day = this_report.getvar("DY")

                # if the SST anomaly differs from the neighbour average
                # by more than the calculated range then reject
                x = this_report.getanom(intype)
                bm = grid.get_buddy_mean(lat, lon, mon, day)
                bsd = grid.get_buddy_stdev(lat, lon, mon, day)

                if abs(x - bm) >= bsd:
                    this_report.set_qc(intype, "bud", 1)
                else:
                    this_report.set_qc(intype, "bud", 0)

            else:
                this_report.set_qc(intype, "bud", 0)

        del grid

        return

    def bayesian_buddy_check(self, intype, stdev1, stdev2, stdev3, parameters):
        """
        Do the Bayesian buddy check. Only those observations that pass the QC_filter
        of the class will be buddy checked. The bayesian buddy check assigns a
        probability of gross error to each observations, which is rounded down to the
        tenth and then multiplied by 10 to yield a flag between 0 and 9.

        :param intype: The variable name for the variable that is to be buddy checked.
        :param stdev1: Field of standard deviations representing standard deviation of difference between
          target gridcell and complete neighbour average (grid area to neighbourhood difference)
        :param stdev2: Field of standard deviations representing standard deviation of difference between
          a single observation and the target gridcell average (point to grid area difference)
        :param stdev3: Field of standard deviations representing standard deviation of difference between
          random neighbour gridcell and full neighbour average (uncertainty in neighbour average)
        :param parameters: list of parameters
        :type intype: string
        :type stdev1: numpy array
        :type stdev2: numpy array
        :type stdev3: numpy array
        """
        assert intype in ["SST", "AT"], "Unknown intype: " + intype

        p0 = parameters["bayesian_buddy_check"]["prior_probability_of_gross_error"]
        q = parameters["bayesian_buddy_check"]["quantization_interval"]
        sigma_m = parameters["bayesian_buddy_check"]["measurement_error"]

        r_hi = parameters[intype]["maximum_anomaly"]  # previous upper QC limits set
        r_lo = -1.0 * r_hi  # previous lower QC limit set

        limits = parameters["bayesian_buddy_check"]["limits"]
        noise_scaling = parameters["bayesian_buddy_check"]["noise_scaling"]

        grid = Np_Super_Ob()
        for rep in self.reps:
            if self.filter.test_report(rep) == 0:
                grid.add_rep(
                    rep.lat(),
                    rep.lon(),
                    rep.getvar("YR"),
                    rep.getvar("MO"),
                    rep.getvar("DY"),
                    rep.getanom(intype),
                )
        grid.take_average()
        grid.get_new_buddy_limits(
            stdev1, stdev2, stdev3, limits, sigma_m, noise_scaling
        )

        for this_report in self.reps:
            if self.filter.test_report(this_report) == 0:
                lat = this_report.lat()
                lon = this_report.lon()
                mon = this_report.getvar("MO")
                day = this_report.getvar("DY")

                # if the SST anomaly differs from the neighbour average
                # by more than the calculated range then reject

                ppp = qc.p_gross(
                    p0,
                    q,
                    r_hi,
                    r_lo,
                    this_report.getanom(intype),
                    grid.get_buddy_mean(lat, lon, mon, day),
                    grid.get_buddy_stdev(lat, lon, mon, day),
                )

                if ppp > 0:
                    flag = int(math.floor(ppp * 10))
                    if flag > 9:
                        flag = 9
                    this_report.set_qc(intype, "bbud", flag)
                else:
                    this_report.set_qc(intype, "bbud", int(0))

            else:
                this_report.set_qc(intype, "bbud", 0)

        del grid

        return

    def get_one_platform_at_a_time(self):
        """
        Generator which yields one Voyage at a time for each unique ID in the Deck.
        Handy for looping over all the ships in the Deck. Only reports that pass the
        QC_filter of the Deck will be returned.

        :return: Yields a class`.Voyage` made of all ships with a single ID.
        :rtype: class`.Voyage`
        """
        for one_id in self.idtracker:
            out_voyage = Voyage()
            for i in self.idtracker[one_id]:
                if self.filter.test_report(self.reps[i]) == 0:
                    out_voyage.add_report(self.reps[i])

            yield out_voyage

    def write_qc(self, runid, icoads_dir, year, month, allvarnames, test=False):
        """
        Write out QC flags for specified variable names from
        the contents of the class`.Deck`.
        """
        count_write = 0
        syr = str(year)
        smn = f"{month:02}"

        if len(self.reps) == 0:
            print("wrote no output")
            return

        for var in allvarnames:
            outfilename = var + "_qc_" + syr + smn + "_" + runid + ".csv"
            if test:
                outfilename = "Test_" + outfilename

            outfile = open(icoads_dir + "/" + outfilename, "w")

            outfile.write(
                self.reps[0].print_qc_block(var, allvarnames[var], header=True)
            )
            for rep in self.reps:
                if rep.getvar("YR") == year and rep.getvar("MO") == month:
                    outfile.write(
                        rep.print_qc_block(var, allvarnames[var], header=False)
                    )
                    count_write += 1

            outfile.close()

        print(f"wrote out {count_write} obs")

    def write_output(self, runid, icoads_dir, year, month, test=False):
        """Write out the contents of the class`.Deck`."""
        count_write = 0
        syr = str(year)
        smn = f"{month:02}"

        outfilename = "Variables_" + syr + smn + "_" + runid + ".csv"
        if test:
            outfilename = "Test_" + outfilename

        outfile = open(icoads_dir + "/" + outfilename, "w")

        varnames = [
            ["ID"],
            ["YR"],
            ["MO"],
            ["DY"],
            ["HR"],
            ["LAT"],
            ["LON"],
            ["AT"],
            ["AT", "anom"],
            ["SST"],
            ["SST", "anom"],
            ["DPT"],
            ["DPT", "anom"],
            ["SLP"],
            ["SLP", "anom"],
            ["OSTIA"],
            ["W"],
            ["D"],
        ]
        if len(self.reps) == 0:
            return
        outfile.write(self.reps[0].print_variable_block(varnames, header=True))
        for rep in self.reps:
            if rep.getvar("YR") == year and rep.getvar("MO") == month:
                outfile.write(rep.print_variable_block(varnames))
                count_write += 1
        outfile.close()

        # write out base QC
        allvarnames = {
            "POS": [
                "day",
                "isship",
                "trk",
                "date",
                "time",
                "pos",
                "blklst",
                "isbuoy",
                "iquam_track",
            ],
            "SST": [
                "bud",
                "clim",
                "nonorm",
                "freez",
                "noval",
                "nbud",
                "bbud",
                "rep",
                "spike",
                "hardlimit",
            ],
            "AT": [
                "bud",
                "clim",
                "nonorm",
                "freez",
                "noval",
                "mat_blacklist",
                "bbud",
                "rep",
                "hardlimit",
            ],
            "DPT": [
                "bud",
                "clim",
                "nonorm",
                "freez",
                "noval",
                "hum_blacklist",
                "bbud",
                "rep",
                "ssat",
                "repsat",
                "round",
                "hardlimit",
            ],
            "SLP": ["bud", "clim", "nonorm", "noval", "rep"],
            "W": ["noval", "hardlimit", "consistency", "wind_blacklist"],
        }

        self.write_qc(runid, icoads_dir, year, month, allvarnames, test=test)

        print(f"wrote out {count_write} obs")

        return

    def write_min_output(self, runid, icoads_dir, year, month, test=False):
        """Write out the contents of the class`.Deck`."""
        count_write = 0
        syr = str(year)
        smn = f"{month:02}"

        outfilename = "Variables_" + syr + smn + "_" + runid + ".csv"
        if test:
            outfilename = "Test_" + outfilename

        outfile = open(icoads_dir + "/" + outfilename, "w")

        varnames = [
            ["ID"],
            ["YR"],
            ["MO"],
            ["DY"],
            ["HR"],
            ["LAT"],
            ["LON"],
            ["AT"],
            ["AT", "anom"],
            ["SST"],
            ["SST", "anom"],
            ["DPT"],
            ["DPT", "anom"],
        ]

        outfile.write(self.reps[0].print_variable_block(varnames, header=True))
        for rep in self.reps:
            if rep.getvar("YR") == year and rep.getvar("MO") == month:
                outfile.write(rep.print_variable_block(varnames))
                count_write += 1
        outfile.close()

        # write out base QC
        allvarnames = {
            "POS": ["day", "isship", "trk", "date", "time", "pos", "blklst", "isbuoy"],
            "SST": ["bud", "clim", "nonorm", "freez", "noval", "nbud", "bbud", "rep"],
            "AT": [
                "bud",
                "clim",
                "nonorm",
                "freez",
                "noval",
                "mat_blacklist",
                "bbud",
                "rep",
            ],
            "DPT": [
                "bud",
                "clim",
                "nonorm",
                "freez",
                "noval",
                "hum_blacklist",
                "bbud",
                "rep",
                "ssat",
                "repsat",
                "round",
            ],
        }

        self.write_qc(runid, icoads_dir, year, month, allvarnames, test=test)

        print(f"wrote out {count_write} obs")

        return
