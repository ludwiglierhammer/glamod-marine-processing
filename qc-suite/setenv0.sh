export home_directory=/gws/nopw/j04/glamod_marine
export home_directory_smf=/gws/smf/j04/c3s311a_lot2
export code_directory=$home_directory_smf/code/marine_code/glamod-marine-processing/qc-suite
export scripts_directory=$code_directory/scripts
export pyEnvironment_directory=$code_directory/pyenvs/env0
export modules_directory=$code_directory/modules
#data_directory=$home_directory/data/datasets/ICOADS_R3.0.0T_original/
export data_directory=$home_directory/data/datasets/ICOADS_R3.0.2T_NRT/ORIGINAL/
#corrections_directory=${home_directory}/data/datasets/NOC_corrections/v1x2019/
export corrections_directory=${home_directory}/data/release_3.0.2/NOC_corrections/v1x2022/
export jobs_directory=${code_directory}/config/jobs2.json
export working_directory=/gws/nopw/j04/glamod_marine/working/r3.0.2/qc-suite/

echo 'Code directory is '$code_directory
echo 'Data directory is '$data_directory
echo 'Corrections directory is '$corrections_directory
echo 'Jobs directory is '$jobs_directory
echo 'Working directory is '$working_directory

# Activate python environment and add jaspy3.7 path to LD_LIBRARY_PATH so that cartopy and other can find the geos library
source $pyEnvironment_directory/bin/activate
export PYTHONPATH="$modules_directory:${PYTHONPATH}"
export LD_LIBRARY_PATH=/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.5.11/envs/jaspy3.7-m3-4.5.11-r20181219/lib/:$LD_LIBRARY_PATH
echo "Python environment loaded from gws: $pyEnvironment_directory"

# Create the scratch directory for the user
scratch_directory=/work/scratch-nopw/$(whoami)
if [ ! -d $scratch_directory ]
then
  echo "Creating user $(whoami) scratch directory $scratch_directory"
  mkdir $scratch_directory
else
  echo "Scratch directory is $scratch_directory"
fi
