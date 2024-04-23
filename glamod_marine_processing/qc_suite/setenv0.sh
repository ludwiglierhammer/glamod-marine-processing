export home_directory=/ichec/work/glamod/glamod-marine-processing.2022

#export home_directory_smf=/gws/smf/j04/c3s311a_lot2
export code_directory=$home_directory/qc-suite
export scripts_directory=$code_directory/scripts
export pyEnvironment_directory=$code_directory/pyenvs/env0
export modules_directory=$code_directory/modules
#data_directory=$home_directory/data/datasets/ICOADS_R3.0.0T_original/
#export data_directory=$home_directory/data/datasets/ICOADS_R3.0.2T_NRT/ORIGINAL/
export data_directory=/ichec/work/glamod/data/marine/datasets/ICOADS_R3.0.2T/ORIGINAL
#corrections_directory=${home_directory}/data/datasets/NOC_corrections/v1x2019/
#export corrections_directory=${home_directory}/data/release_3.0.2/NOC_corrections/v1x2022/
export corrections_directory=/ichec/work/glamod/data/marine/release_6.0/NOC_corrections
export config_directory=${code_directory}/config
export working_directory=/ichec/work/glamod/glamod-marine-processing.2022/working/qc-suite/release_6.0
export qc_log_directory=${working_directory}/logs_qc
export qc_hr_log_directory=${working_directory}/logs_qc_hr

#/gws/nopw/j04/glamod_marine/working/r3.0.2/qc-suite/

echo 'Code directory is '$code_directory
echo 'Data directory is '$data_directory
echo 'Corrections directory is '$corrections_directory
echo 'Config directory is '$config_directory
echo 'Working directory is '$working_directory

# Activate python environment and add jaspy3.7 path to LD_LIBRARY_PATH so that cartopy and other can find the geos library
source activate $pyEnvironment_directory
export PYTHONPATH="$modules_directory:${PYTHONPATH}"
export LD_LIBRARY_PATH=/ichec/packages/conda/2/lib/:$LD_LIBRARY_PATH
echo "Python environment loaded from gws: $pyEnvironment_directory"

# Create the scratch directory for the user
scratch_directory=/ichec/work/glamod/$(whoami)
if [ ! -d $scratch_directory ]
then
  echo "Creating user $(whoami) scratch directory $scratch_directory"
  mkdir $scratch_directory
else
  echo "Scratch directory is $scratch_directory"
fi
