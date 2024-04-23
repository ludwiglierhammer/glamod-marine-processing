#!/bin/bash

export home_directory=/ichec/work/glamod/glamod-marine-processing.2022
#export home_directory_smf=/gws/smf/j04/c3s311a_lot2
export code_directory=$home_directory/obs-suite
export config_directory=$code_directory/configuration_files

export pyTools_directory=$code_directory/modules/python
export scripts_directory=$code_directory/scripts
export lotus_scripts_directory=$code_directory/lotus_scripts
#export data_directory=$home_directory/data
export data_directory=/ichec/work/glamod/data/marine

echo 'Data directory is '$data_directory
echo 'Code directory is '$code_directory
echo 'Config directory is '$config_directory
# Create the scratch directory for the user
export scratch_directory=/ichec/work/glamod/$(whoami)
if [ ! -d $scratch_directory ]
then
  echo "Creating user $(whoami) scratch directory $scratch_directory"
  mkdir $scratch_directory
else
  echo "Scratch directory is $scratch_directory"
fi
