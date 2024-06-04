"""Module to transfrom old file with periods to new format."""

from __future__ import annotations

import os

work = "/ichec/work/glamod/"
file_in = (
    work
    + "glamod-marine-processing.2022/obs-suite/configuration_files/release_4.0-000000/ICOADS_R3.0.0T/source_deck_list.txt"
)
data_dir = work + "data/marine/release_4.0/ICOADS_R3.0.0T/level2/"
file_out = (
    work
    + "glamod-marine-processing.2022/obs-suite/configuration_files/release_4.0-000000/ICOADS_R3.0.0T/source_deck_periods_fromdata.json"
)

with open(file_in) as periods_fh:
    lines = periods_fh.readlines()
    with open(file_out, "w") as periods_new:
        periods_new.writelines("{\n")
        for sid_line in lines:
            lastline = sid_line == lines[-1]
            sid_dck = sid_line.rstrip()
            year_init = 3000
            year_end = 0
            print(f"sid: {sid_dck}")
            sid_dir = os.path.join(data_dir, sid_dck)
            if os.path.isdir(sid_dir):
                for file in os.listdir(sid_dir):
                    table = file.rsplit("-")[0]
                    if table == "header":
                        year = int(file.rsplit("-")[1])
                        year_init = min(year, year_init)
                        year_end = max(year, year_end)
                        if year_end < 1:
                            year_init = 0  # no data, set both to zero
                print(year_init)
                print(year_end)
                periods_new.writelines(f'  "{sid_dck}": {{\n')
                periods_new.writelines(f'    "year_init": {year_init},\n')
                periods_new.writelines(f'    "year_end": {year_end}\n')
                if not lastline:
                    periods_new.writelines("  },\n")
                else:
                    periods_new.writelines("  }\n")
        periods_new.writelines("}\n")
