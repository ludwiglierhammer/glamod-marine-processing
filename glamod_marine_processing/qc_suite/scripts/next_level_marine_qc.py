from pathlib import Path
import os
import datetime

import cartopy.crs
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import numpy as np
import pandas as pd

from cdm_reader_mapper import read_mdf
from cdm_reader_mapper.data import test_data

from glamod_marine_processing.qc_suite.modules.external_clim import (
    Climatology,
    inspect_climatology,
)

from glamod_marine_processing.qc_suite.modules.next_level_qc import (
    do_climatology_check,
    do_date_check,
    do_day_check,
    do_hard_limit_check,
    do_missing_value_check,
    do_missing_value_clim_check,
    do_position_check,
    do_sst_freeze_check,
    do_supersaturation_check,
    do_time_check,
    do_wind_consistency_check,
)
from glamod_marine_processing.qc_suite.modules.next_level_track_check_qc import (  # find_saturated_runs,
    do_few_check,
    do_iquam_track_check,
    do_spike_check,
    do_track_check,
    find_repeated_values,
)
from glamod_marine_processing.qc_suite.modules.next_level_deck_qc import (
    mds_buddy_check,
)


@inspect_climatology("climatology")
def calculate_anomalies(value, climatology, **kwargs):
    anomaly = value - climatology
    return anomaly


def fix_cdm(db_cdm):
    db_cdm.data = db_cdm.replace("null", None)

    tables = [
        "header",
        "observations-sst",
        "observations-at",
        "observations-slp",
    ]

    for table in tables:

        db_cdm.data[(table, "latitude")] = db_cdm[(table, "latitude")].astype(float)
        db_cdm.data[(table, "longitude")] = db_cdm[(table, "longitude")].astype(float)

        if table == "header":

            ids = db_cdm.data[(table, "primary_station_id")]
            for i, id in enumerate(ids):
                if id is None:
                    ids[i] = "        "
            db_cdm.data[(table, "primary_station_id")] = ids

            db_cdm.data[(table, "report_timestamp")] = pd.to_datetime(
                db_cdm[(table, "report_timestamp")],
                format="%Y-%m-%d %H:%M:%S",
                errors="coerce",
            )

            db_cdm.data[(table, "station_speed")] = db_cdm[
                (table, "station_speed")
            ].astype(float)

            db_cdm.data[(table, "station_course")] = db_cdm[
                (table, "station_course")
            ].astype(float)

        else:
            db_cdm.data[(table, "observation_value")] = db_cdm[
                (table, "observation_value")
            ].astype(float)

            db_cdm.data[(table, "date_time")] = pd.to_datetime(
                db_cdm[(table, "date_time")],
                format="%Y-%m-%d %H:%M:%S",
                errors="coerce",
            )

    return db_cdm


import gzip
import shutil
from pathlib import Path

data_dir = Path(os.getenv("DATADIR"))


print("Start")
print(datetime.datetime.now())

# Read in the climatology
data_dir = os.getenv("DATADIR")
# clim_file_names = []
# for i in range(365):
#     new_output_file = Path(data_dir) / "SST_CCI_climatology" / f"D{i + 1:03d}.nc"
#     clim_file_names.append(new_output_file)
# sst_clim = Climatology.open_netcdf_file(clim_file_names, 'analysed_sst')
sst_clim = Climatology.open_netcdf_file(
    Path(data_dir) / "QCClimatologies" / "AT_pentad_climatology.nc",
    "at",
    time_axis="pentad_time",
    lat_axis="latitude",
    lon_axis="longitude",
    source_units="degC",
    target_units="K",
)
# sst_clim = Climatology.open_netcdf_file(
#     Path(data_dir) / "SST_CCI_climatology" / "SST_1x1_daily.nc",
#     "sst",
#     time_axis="time",
#     lat_axis="latitude",
#     lon_axis="longitude",
# )

print("Read SST climatology")
print(datetime.datetime.now())

imodel = "icoads"
encoding = "cp1252"


single_file = Path(data_dir) / "ICOADS" / "cat.txt"

with open(single_file, "w") as outfile:
    filepaths = [
        Path(data_dir) / "ICOADS" / "IMMA1_R3.0.0_1850-01.gz",
        # Path(data_dir) / "ICOADS" / "IMMA1_R3.0.0_1850-02.gz",
        # Path(data_dir) / "ICOADS" / "IMMA1_R3.0.0_1850-03.gz",
    ]
    for fname in filepaths:
        with gzip.open(fname, "rb") as f_in:
            with open(str(fname).replace(".gz", ""), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        with open(str(fname).replace(".gz", "")) as f:
            for line in f:
                outfile.write(line)
# single_file = data_dir / "ICOADS" / "IMMA1_R3.0.0_1899-01"

print("Preprocessed IMMA files, gunzipped, concatenated etc.")
print(datetime.datetime.now())

db_imma = read_mdf(single_file, imodel=imodel, encoding=encoding)
db_cdm = db_imma.map_model()


print("Read IMMA files")
print(datetime.datetime.now())

# Fix missing hours
hours = db_imma.data[("core", "HR")].values
hours[np.isnan(hours)] = 0.0
db_imma.data[("core", "HR")].values[:] = hours

db_cdm = db_imma.map_model()

db_cdm = fix_cdm(db_cdm)

header = db_cdm.data["header"].sort_values(by=["primary_station_id", "report_id"])
obs_sst = db_cdm.data["observations-sst"].sort_values(by="report_id")
obs_at = db_cdm.data["observations-at"].sort_values(by="report_id")

print("Read everything in IMMAwise")
print(datetime.datetime.now())


# read in SST stdev climatology
at_stdev_clim_file = (
    Path(data_dir) / "QCClimatologies" / "HadSST2_pentad_stdev_climatology.nc"
)
at_stdev_clim = Climatology.open_netcdf_file(
    at_stdev_clim_file, "sst", time_axis="time"
)

print("Read SST temperature stdev clim")
print(datetime.datetime.now())

sst_anomalies = obs_sst.apply(
    lambda row: calculate_anomalies(
        value=row["observation_value"],
        climatology=sst_clim,
        lat=row["latitude"],
        lon=row["longitude"],
        date=row["date_time"],
    ),
    axis=1,
)

print("Calculated anomalies")
print(datetime.datetime.now())

groups = header.groupby("primary_station_id", group_keys=False)
results = groups.apply(
    lambda track: pd.Series(
        do_track_check(
            vsi=track["station_speed"],
            dsi=track["station_course"],
            lat=track["latitude"],
            lon=track["longitude"],
            date=track["report_timestamp"],
            ids=track.name,
            max_direction_change=60.0,
            max_speed_change=10.0,
            max_absolute_speed=40.0,
            max_midpoint_discrepancy=150.0,
        )
    ),
    include_groups=False,
)
results = results.explode()
results.index = header.index
track_check_qc = results.values.astype(int)

print("Run track checks")
print(datetime.datetime.now())

# Buddy check
limits = [[1, 1, 2], [2, 2, 2], [1, 1, 4], [2, 2, 4]]
number_of_obs_thresholds = [[0, 5, 15, 100], [0], [0, 5, 15, 100], [0]]
multipliers = [[4.0, 3.5, 3.0, 2.5], [4.0], [4.0, 3.5, 3.0, 2.5], [4.0]]

selection = ~np.isnan(sst_anomalies)
lats = obs_sst["latitude"].values[selection]
lons = obs_sst["longitude"].values[selection]
dates = obs_sst["date_time"][selection].reset_index().date_time

buddy_check = mds_buddy_check(
    lats,
    lons,
    dates,
    sst_anomalies[selection],
    at_stdev_clim,
    limits,
    number_of_obs_thresholds,
    multipliers,
)

buddy_check_filled = np.zeros(len(sst_anomalies)) + 2.0
buddy_check_filled[selection] = buddy_check[:]
buddy_check = buddy_check_filled

print("Ran buddy checks")
print(datetime.datetime.now())


position_check_qc = do_position_check(lat=header["latitude"], lon=header["longitude"])

day_check = do_day_check(
    date=header["report_timestamp"],
    lat=header["latitude"],
    lon=header["longitude"],
)

sst_climatology_check = do_climatology_check(
    value=obs_sst["observation_value"],
    climatology=sst_clim,
    maximum_anomaly=8.0,  # K
    lat=obs_sst["latitude"],
    lon=obs_sst["longitude"],
    date=obs_sst["date_time"],
)

sst_missing_check = do_missing_value_check(value=obs_sst["observation_value"])

sst_freeze_check = do_sst_freeze_check(
    sst=obs_sst["observation_value"],
    freezing_point=271.35,
    freeze_check_n_sigma=2.0
)

sst_hard_limit = do_hard_limit_check(
    value=obs_sst["observation_value"],
    limits=[268.15, 318.15],
)



print("Ran single obs checks")
print(datetime.datetime.now())


obs_sst["anom"] = sst_anomalies
obs_sst["mdi"] = sst_missing_check
obs_sst["fc"] = sst_freeze_check
obs_sst["hl"] = sst_hard_limit
obs_sst["clim"] = sst_climatology_check
obs_sst["bud"] = buddy_check

header["tc"] = track_check_qc

obs_sst = obs_sst[obs_sst["report_id"].notna()]

combined = pd.merge(header, obs_sst, how="left", on="report_id")

combined[["mdi", "fc", "hl", "clim", "bud"]] = combined[
    ["mdi", "fc", "hl", "clim", "bud"]
].fillna(value=2)
combined[["tc"]] = combined[["tc"]].fillna(value=2)

track_check_qc = combined["tc"].values
sst_hard_limit = combined["hl"].values
sst_missing_check = combined["mdi"].values
sst_freeze_check = combined["fc"].values
sst_climatology_check = combined["clim"].values
sst_buddy_check = combined["bud"].values

lats = combined["latitude_x"]
lats2 = combined["latitude_y"]
lons = combined["longitude_x"]
lons2 = combined["longitude_y"]
ssts = combined["observation_value"] - 273.15
anoms = combined["anom"]

colors = np.array([[0, 0, 0] for _ in range(len(lats))])
colors[track_check_qc != 0] = [1, 0, 0]
colors[sst_climatology_check != 0] = [0, 1, 0]
colors[sst_freeze_check != 0] = [0, 0, 1]
colors[sst_hard_limit != 0] = [0.5, 0.5, 0.0]
colors[sst_missing_check != 0] = [0.1, 0.1, 0.1]
colors[sst_buddy_check == 1] = [0, 1, 1]

id_list = combined["primary_station_id"].unique()

plot_all_tracks = True
if plot_all_tracks:
    for id0 in id_list:
        subset = combined[combined["primary_station_id"] == id0]
        lats0 = subset["latitude_x"]
        lons0 = subset["longitude_x"]
        tcqc = subset["tc"]

        if max(tcqc) == 0:
            continue

        min_lon = min(lons0) - 3
        max_lon = max(lons0) + 3

        min_lat = min(lats0) - 3
        max_lat = max(lats0) + 3

        colors0 = np.array([[0, 0, 0] for _ in range(len(lats0))])
        colors0[tcqc == 1] = [1, 0, 0]
        colors0[tcqc == 2] = [0, 1, 0]
        colors0[tcqc == 3] = [0, 0, 1]

        sizes0 = np.array([25 for _ in range(len(lats0))])
        sizes0[0] = 50

        fig = plt.figure(figsize=(20, 10))
        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0))
        ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())
        ax.coastlines(linewidth=1, color="#cccccc")
        ax.plot(lons0, lats0, alpha=0.5, transform=ccrs.PlateCarree())
        ax.scatter(
            lons0, lats0, c=colors0, s=sizes0, alpha=0.5, transform=ccrs.PlateCarree()
        )
        plt.title(id0)
        plt.show()
        plt.close()


print(datetime.datetime.now())

fig = plt.figure(figsize=(20, 10))
ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0))
ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())
ax.coastlines(linewidth=1, color="#cccccc")
ax.scatter(lons, lats, c=colors, s=5, alpha=0.5, transform=ccrs.PlateCarree())
plt.show()
plt.close()

fig, axs = plt.subplots(2, 3)

axs[0][0].scatter(lons, lats, c=colors, s=5, alpha=0.2)
axs[0][0].set_xlim(-180, 180)
axs[0][0].set_ylim(-70, 70)

axs[0][1].scatter(ssts, lats, c=colors, s=5, alpha=0.2)
axs[0][1].set_xlim(-7, 35)
axs[0][1].set_ylim(-70, 70)

axs[1][0].scatter(anoms, ssts, c=colors, s=5, alpha=0.2)
axs[1][0].set_xlim(-10, 10)
axs[1][0].set_ylim(-7, 35)

axs[0][2].scatter(
    ssts,
    track_check_qc
    + sst_hard_limit
    + sst_missing_check
    + sst_freeze_check
    + sst_climatology_check,
    c=colors,
    s=25,
    alpha=0.2,
)

axs[1][1].scatter(anoms, lats, c=colors, s=5, alpha=0.2)
axs[1][1].set_xlim(-10, 10)
axs[1][1].set_ylim(-70, 70)

axs[1][2].hist(ssts, bins=100)

plt.show()
