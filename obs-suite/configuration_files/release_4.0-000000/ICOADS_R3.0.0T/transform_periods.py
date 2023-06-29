#!/bin/bash python3

#just to transform old fie with periods to new format

file_in="/ichec/work/glamod/glamod-marine-processing.2022/obs-suite/configuration_files/release_4.0-000000/ICOADS_R3.0.2T_NRT/periods_initial.txt"
file_out = "/ichec/work/glamod/glamod-marine-processing.2022/obs-suite/configuration_files/release_4.0-000000/ICOADS_R3.0.2T_NRT/source_deck_periods.txt"

with open(file_in, 'r') as periods_fh:
  lines = periods_fh.readlines()
  with open(file_out, 'w') as periods_new:
    periods_new.writelines('{\n')
    for sid_line in lines:
      lastline = sid_line==lines[-1]
      sid_dck, time_init, time_end = sid_line.rsplit(' ')
      #print('sid: {}; time1: {}; time2: {}'.format(sid_dck, time_init, time_end))
      periods_new.writelines('  \"{0}\": {{\n'.format(sid_dck))
      periods_new.writelines('    \"year_init\": {0},\n'.format(time_init.rsplit('-')[0]))
      periods_new.writelines('    \"year_end\": {0}\n'.format(time_end.rsplit('-')[0]))
      if not lastline:
        periods_new.writelines('  },\n')
      else:
        periods_new.writelines('  }\n')
    periods_new.writelines('}\n')
