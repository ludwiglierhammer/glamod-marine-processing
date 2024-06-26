"""
Set of functions for processing files and filenames which may be system specific and might need to be
changed in moving from one system to another.
"""

from __future__ import annotations

import os


def process_bad_id_file(bad_id_file):
    """
    Read in each entry in the bad id file and if it is shorter than 9 characters
    pad with white space at the end of the string
    """
    idfile = open(bad_id_file)
    ids_to_exclude = []
    for line in idfile:
        line = line.rstrip()
        while len(line) < 9:
            line = line + " "
        if line != "         ":
            ids_to_exclude.append(line)
    idfile.close()
    return ids_to_exclude


def build_completions(indir, subdirs):
    """
    Given a string and a list of string return a list which cumulatively adds each string in the list to the base string
    separating each additional string with a slash (or operating system approved directory divider).

    :param indir: base string
    :param subdirs: list of strings to badded
    :type indir: string
    :type subdirs: list[string]
    :return: list of completed strings
    :rtype: list[string]
    """
    base_dir = indir + ""
    completions = []
    for asubdir in subdirs:
        base_dir = os.path.join(base_dir, asubdir)
        completions.append(base_dir)

    return completions


def safe_make_dir_generic(out_dir, subdirs):
    """
    Build subdirectories of various kinds from a base directory and a list of desired subdirectories

    :param out_dir: base directory in which to build the subdirectories
    :param subdirs: a list of the names of the desired subdirectories
    :return: directory name
    """
    completions = build_completions(out_dir, subdirs)

    adir = None

    for adir in completions:
        try:
            os.mkdir(adir)
            print(f"Directory {adir} created ")
        except OSError:
            print(f"Directory {adir} already exists")

    return adir


def safe_make_dir(out_dir, year, month):
    """
    Build subdirectories of year and month within out_dir unless these already exist

    :param out_dir: base directory to build year and month sub directories in
    :param year: year for subdirectory name
    :param month: month for subdirectory name
    :return: full pathname of created directory
    """
    syr = str(year)
    smn = f"{month:02}"

    d2 = safe_make_dir_generic(out_dir, [syr, smn])

    return d2


def icoads_filename_from_stub(dirstubs, filenamestubs, year, month):
    """
    Build ICOADS filename from stubs. Choose the first filled filename that exists

    :param dirstubs: list of directories with placeholders for years, YYYY, and month, MMMM
    :param filenamestubs: list of filenames with placeholders for years, YYYY, and months, MMMM
    :param year: year for file
    :param month: month for file
    :return: completed file name
    """
    if year is None or month is None:
        return None

    assert len(dirstubs) == len(
        filenamestubs
    ), "dirstubs and filename stubs have different numbers of members"

    candidatefilenames = []

    for i, dirstub in enumerate(dirstubs):
        filenamestub = filenamestubs[i]
        candidatefilenames.append(make_filename(dirstub, filenamestub, year, month, 1))

    outfilename = None
    for fname in candidatefilenames:
        if outfilename is None:
            if os.path.isfile(fname):
                outfilename = fname

    return outfilename


def icoads_filename(icoads_dir, readyear, readmonth, version):
    """
    Build the filename for an ICOADS file

    :param icoads_dir: the base directory containing the ICOADS data
    :param readyear: the year to read in
    :param readmonth: the month to read in
    :param version: the version of ICOADS being used
    :return: full pathname for the ICOADS file for specified year and month
    """
    assert version in ["2.5", "3.0"], "name not 2.5 or 3.0"

    syr = str(readyear)
    smn = f"{readmonth:02}"

    filename = None

    if version == "2.5":
        filename = f"{icoads_dir}/ICOADS.2.5.1/R2.5.1.{syr}.{smn}.gz"
        if (readyear > 2007) & (readyear < 2015):
            filename = f"{icoads_dir}/R2.5.2.{syr}.{smn}.gz"

    if version == "3.0":
        if readyear <= 2014:
            filename = f"{icoads_dir}/ICOADS.3.0.0/IMMA1_R3.0.0_{syr}-{smn}.gz"
        if readyear >= 2015:
            filename = f"{icoads_dir}/ICOADS.3.0.1/IMMA1_R3.0.1_{syr}-{smn}.gz"

    return filename


def process_string(instring, year, month, day):
    """
    Process a string replacing placeholder occurrences of YYYY with year, MMMM with month and DDDD with day.

    :param instring: string to be converted
    :param year: year to replace in input string
    :param month: month to replace in input string
    :param day: day to replace in input string
    :return: string with filled placeholders.
    """
    sy = f"{year:04}"
    sm = f"{month:02}"
    sd = f"{day:02}"

    outstring = instring.replace("YYYY", sy)
    outstring = outstring.replace("MMMM", sm)
    outstring = outstring.replace("DDDD", sd)

    return outstring


def make_filename(dirstub, filenamestub, year, month, day):
    """
    Build a filename from a particular directory stub and filename stub. Stubs have the year month and day coded
    as YYYY MMMM and DDDD respectively.

    :param dirstub: directory stub with placeholders for year (YYYY) month (MMMM) and day (DDDD)
    :param filenamestub: filename stub with placeholders for year (YYYY) month (MMMM) and day (DDDD)
    :param year: year to construct filename for
    :param month: month to construct filename for
    :param day: day to construct filename for
    :return: completed pathname for file
    """
    dirfill = process_string(dirstub, year, month, day)
    filenamefill = process_string(filenamestub, year, month, day)

    filename = os.path.join(dirfill, filenamefill)

    return filename


def get_background_filename(dirstubs, filenamestubs, year, month, day):
    """
    Construct a background file filename. A background file is an OSTIA SST field used in the tracking_qc.py. The
    filename is built from directory stubs and filename stubs, which are filled with the specified year month and day.
    If necessary it will bunzip to the files to a scratch folder specified by the environment variable SCRATCH.
    Note that dirstubs and filenamestubs are both lists. The function will use the first of these in preference, but
    if the generated filename does not exist, it will move down the list.

    :param dirstubs: list of directory name stubs
    :param filenamestubs: list of filename stubs
    :param year: year to construct filename for
    :param month: month to construct filename for
    :param day: day to construct filename for
    :return: filled background field filename
    """
    if year is None or month is None or day is None:
        return None
    if isinstance(dirstubs, str):
        dirstubs = [dirstubs]
    if isinstance(filenamestubs, str):
        filenamestubs = [filenamestubs]
    assert len(dirstubs) == len(
        filenamestubs
    ), "dirstubs and filename stubs have different numbers of members"

    originalfilenames = []

    for i, dirstub in enumerate(dirstubs):
        filenamestub = filenamestubs[i]
        originalfilenames.append(make_filename(dirstub, filenamestub, year, month, day))

    # find the first original file that exists in the list
    chosen_orig = None
    for i, fname in enumerate(originalfilenames):
        if chosen_orig is None:
            if os.path.isfile(fname) and os.stat(fname).st_size != 0:
                chosen_orig = fname

    if chosen_orig is None:
        return None

    outfile = chosen_orig

    return outfile
