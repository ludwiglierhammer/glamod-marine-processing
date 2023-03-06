#!/bin/bash

export home_directory=/ichec/work/glamod/glamod-marine-processing.2022
#export home_directory_smf=/gws/smf/j04/c3s311a_lot2
export code_directory=$home_directory/metadata-suite
#export config_directory=$code_directory/configuration_files

#export pyTools_directory=$code_directory/modules/python
export scripts_directory=$code_directory/scripts
#export lotus_scripts_directory=$code_directory/lotus_scripts
#export data_directory=$home_directory/data
#export data_directory=/ichec/work/glamod/data/marine

#home_directory=/group_workspaces/jasmin2/glamod_marine
#home_directory_smf=/gws/smf/j04/c3s311a_lot2
#code_directory=$home_directory_smf/code/marine_code/glamod-marine-processing/metadata-suite
export scripts_directory=$code_directory/scripts
export pyEnvironment_directory=$code_directory/pyenvs/env1
export modules_directory=$code_directory/modules

echo 'Code directory is '$code_directory

# Activate python environment and add jaspy3.7 path to LD_LIBRARY_PATH so that cartopy and other can find the geos library
source activate $pyEnvironment_directory
export PYTHONPATH="$modules_directory:${PYTHONPATH}"
export LD_LIBRARY_PATH=/ichec/packages/conda/2/lib/:$LD_LIBRARY_PATH
#/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.5.11/envs/jaspy3.7-m3-4.5.11-r20181219/lib/:$LD_LIBRARY_PATH
echo "Python environment loaded from: $pyEnvironment_directory"

# Create the scratch directory for the user
#scratch_directory=/work/scratch-nompiio/$(whoami)
export scratch_directory=/ichec/work/glamod/$(whoami)
if [ ! -d $scratch_directory ]
then
  echo "Creating user $(whoami) scratch directory $scratch_directory"
  mkdir $scratch_directory
else
  echo "Scratch directory is $scratch_directory"
fi
