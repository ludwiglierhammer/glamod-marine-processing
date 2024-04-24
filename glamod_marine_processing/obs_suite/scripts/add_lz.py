"""ADD lz module."""

from __future__ import annotations

import time

fpath = "/ichec/work/glamod/data/marine/datasets/ICOADS_R3.0.2T/ORIGINAL/"
# fpath= "/ichec/work/glamod/data/marine/datasets/ICOADS_R3.0.2T/level0/172-798/"
# fpath_out= "/ichec/work/glamod/data/marine/release_6.0/LZ_UIDS/"
fpath_out = "/ichec/home/users/awerneck/LZ_UIDS/"
print("Reading from: " + fpath)
print("Writing to: " + fpath_out)
# ds=IMMA.get(fpath)
# ds=open(fpath)
for year in range(2021, 2023):
    for mon in range(1, 13):
        fn = f"IMMA1_R3.0.2T_{year}-{mon:02d}"
        print(fn)
        with open(fpath + fn) as ds:
            with open(fpath_out + f"lz_{year}-{mon:02d}.psv", "w") as outfile:
                for line in ds.readlines():
                    # print(line[170])
                    if line[170] == "1":
                        UID = line.rsplit("9815")[1][:6]
                        # UID = line[325:335]
                        # print(UID)
                        # print(line)
                        # if UID[:4]!='9815':#check for correct attachement (C98)
                        #    raise ValueError()
                        # else:
                        outfile.writelines(f"ICOADS-302-{UID}\n")
                        time.sleep(0.1)
                    # UID = line[34:43]
                    # print(line[34:43])
