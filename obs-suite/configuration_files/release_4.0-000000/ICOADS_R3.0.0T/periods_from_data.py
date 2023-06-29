#!/bin/bash python3

#just to transform old fie with periods to new format
import os

file_in="/ichec/work/glamod/glamod-marine-processing.2022/obs-suite/configuration_files/release_4.0-000000/ICOADS_R3.0.0T/source_deck_list.txt"
data_dir="/ichec/work/glamod/data/marine/release_4.0/ICOADS_R3.0.0T/level2/"
file_out = "/ichec/work/glamod/glamod-marine-processing.2022/obs-suite/configuration_files/release_4.0-000000/ICOADS_R3.0.0T/source_deck_periods_fromdata.json"

with open(file_in, 'r') as periods_fh:
  lines = periods_fh.readlines()
  with open(file_out, 'w') as periods_new:
    periods_new.writelines('{\n')
    for sid_line in lines:
      lastline = sid_line==lines[-1]
      sid_dck = sid_line.rstrip()
      year_init = 3000
      year_end = 0
      print('sid: {}'.format(sid_dck))
      sid_dir=os.path.join(data_dir, sid_dck)
      if os.path.isdir(sid_dir):
        for file in os.listdir(sid_dir):
          table=file.rsplit('-')[0]
          if table == 'header':
            year = int(file.rsplit('-')[1])
            year_init = min(year, year_init)
            year_end = max(year, year_end)
            if year_end<1: year_init=0 #no data, set both to zero
        print(year_init)
        print(year_end)
        periods_new.writelines('  \"{0}\": {{\n'.format(sid_dck))
        periods_new.writelines('    \"year_init\": {0},\n'.format(year_init))
        periods_new.writelines('    \"year_end\": {0}\n'.format(year_end))
        if not lastline:
          periods_new.writelines('  },\n')
        else:
          periods_new.writelines('  }\n')
    periods_new.writelines('}\n')
