"""Split original ICOADS data into monthly source and deck files."""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path

# number of lines to store in each cache
maxLines = 1000
# columns for resepective variables
dckIdx = range(118, 121)
sidIdx = range(121, 124)
platformTypeIdx = range(124, 126)
callsignIdx = range(34, 43)
yearIdx = range(0, 4)
monthIdx = range(4, 6)
dayIdx = range(6, 8)
hourIdx = range(8, 12)
latitudeIdx = range(12, 17)
longitudeIdx = range(17, 23)
# default input file source pattern
_source_pattern = "IMMA1_R3.0.*"


def get_cell(lon, lat, xmin, xmax, xstep, ymin, ymax, ystep):
    """Get lat-lon cell."""
    nx = int((xmax - xmin) // xstep)
    xind = int((lon - xmin) // xstep)
    yind = int((lat - ymin) // ystep)
    cell = nx * yind + xind
    x1 = xind * xstep
    x2 = (xind + 1) * xstep
    y1 = yind * ystep
    y2 = (yind + 1) * ystep
    cell = {"id": cell, "xmin": x1, "xmax": x2, "ymin": y1, "ymax": y2, "count": 0}
    return cell


class deck_store:
    """Class to store info for each source / deck."""

    def __init__(self, tag, basepath, filename):
        Path(f"{basepath}/{tag}").mkdir(parents=True, exist_ok=True)
        self.outfile = f"{basepath}/{tag}/{os.path.basename(filename)}"
        self.count = 0
        self.linecache = list()
        self.fh = open(self.outfile, "w")
        self.summary = dict()
        self.summary["bbox"] = dict()
        self.summary["bbox"]["minLongitude"] = 360
        self.summary["bbox"]["maxLongitude"] = -360
        self.summary["bbox"]["minLatitude"] = 90
        self.summary["bbox"]["maxLatitude"] = -90
        self.summary["callsigns"] = dict()
        self.summary["platforms"] = dict()
        self.summary["year"] = dict()
        self.summary["dck"] = dict()

    def set_path(self, tag, basepath, filename):
        """Set data path."""
        outfile = f"{basepath}/{tag}/{os.path.basename(filename)}"
        if self.outfile != outfile:
            self.close()
            self.outfile = outfile
            self.fh = open(self.outfile, "w")

    def add_line(self, line):
        """Extract the data to be used when summarising deck."""
        latitude = float(line[latitudeIdx.start : latitudeIdx.stop]) * 0.01
        longitude = float(line[longitudeIdx.start : longitudeIdx.stop]) * 0.01
        if longitude >= 180:
            longitude = longitude - 360
        year = int(line[yearIdx.start : yearIdx.stop])
        dck = line[dckIdx.start : dckIdx.stop]
        platform = line[platformTypeIdx.start : platformTypeIdx.stop]
        callsign = line[callsignIdx.start : callsignIdx.stop]
        cell = get_cell(longitude, latitude, -180, 180, 5, -90, 90, 5)

        if callsign in self.summary["callsigns"]:
            self.summary["callsigns"][callsign] += 1
        else:
            self.summary["callsigns"][callsign] = 1

        if platform in self.summary["platforms"]:
            self.summary["platforms"][platform] += 1
        else:
            self.summary["platforms"][platform] = 1

        if year in self.summary["year"]:
            self.summary["year"][year]["count"] += 1
        else:
            self.summary["year"][year] = dict()
            self.summary["year"][year]["count"] = 1

        if cell["id"] not in self.summary["year"][year]:
            self.summary["year"][year][cell["id"]] = cell
        self.summary["year"][year][cell["id"]]["count"] += 1

        if dck in self.summary["dck"]:
            self.summary["dck"][dck] += 1
        else:
            self.summary["dck"][dck] = 1

        self.linecache.append(line)
        self.count += 1

        # add summary statistics

        self.summary["bbox"]["minLatitude"] = min(
            self.summary["bbox"]["minLatitude"], latitude
        )
        self.summary["bbox"]["maxLatitude"] = max(
            self.summary["bbox"]["maxLatitude"], latitude
        )

        # add summary statistics

        self.summary["bbox"]["minLongitude"] = min(
            self.summary["bbox"]["minLongitude"], longitude
        )
        self.summary["bbox"]["maxLongitude"] = max(
            self.summary["bbox"]["maxLongitude"], longitude
        )

        if len(self.linecache) == maxLines:
            self.writeCache()

    def writeCache(self):
        """Write line cache."""
        self.fh.writelines(self.linecache)
        self.linecache = list()

    def close(self):
        """Close file."""
        self.writeCache()
        self.fh.close()


def pre_processing(
    idir,
    odir,
    source_pattern="IMMA1_R3.0.*",
    overwrite=False,
):
    """Split ICOADS data into monthly deck files.

    Parameters
    ----------
    idir: str
        Input data directory
    odir: str
        Output data directory
    overwrite: bool
        If True, overwrite already existing files.
    """
    # get list of files to process
    if source_pattern is None:
        source_pattern = _source_pattern
    infiles = sorted(glob.glob(f"{idir}/{source_pattern}"))
    # get number of files
    nfiles = len(infiles)
    print(f"{nfiles} files found in foler {idir}")
    # initialise dictionary to store data
    decks = dict()
    # now iterate over files
    for infile in infiles:
        # get current file to process
        print(f"Pre-Processing {infile}")
        fh = open(infile, encoding="cp1252")

        for line in fh.readlines():
            # get source Id and deck
            dck = int(line[dckIdx.start : dckIdx.stop])
            sid = int(line[sidIdx.start : sidIdx.stop])
            # set tag for data
            tag = f"{sid:03d}-{dck:03d}"
            # Initialise deck or update output path
            if tag not in decks:
                decks[tag] = deck_store(tag, odir, infile)
            else:
                decks[tag].set_path(tag, odir, infile)
            # add ICOADS record to deck
            decks[tag].add_line(line)
        fh.close()

    # now make sure all files are closed and write summaries to file
    for dck in decks:
        with open(f"{dck}.json", "w") as ofh:
            json.dump(decks[dck].summary, ofh)
        decks[dck].close()
