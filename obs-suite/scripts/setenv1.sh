home_directory=/gws/nopw/j04/c3s311a_lot2/
home_directory_smf=/gws/smf/j04/c3s311a_lot2/
code_directory=$home_directory/code/marine_code/glamod-marine-processing/obs-suite
code_directory_smf=$home_directory_smf/code/marine_code/glamod-marine-processing/obs-suite
data_directory=$home_directory/data/marine
pyTools_directory=$code_directory/modules/python
scripts_directory=$code_directory/scripts
pyEnvironment_directory=$code_directory_smf/pyenvs/env1
MD_directory=$data_directory/r092019/Pub47

# Activate python environment and add jaspy3.7 path to LD_LIBRARY_PATH so that cartopy and other can find the geos library
echo "Python environment loaded from gws: $pyEnvironment_directory"
source $pyEnvironment_directory/bin/activate
export PYTHONPATH="$pyTools_directory:${PYTHONPATH}"
export LD_LIBRARY_PATH=/apps/contrib/jaspy/miniconda_envs/jaspy3.7/m3-4.5.11/envs/jaspy3.7-m3-4.5.11-r20181219/lib/:$LD_LIBRARY_PATH

# Create the scratch directory for the user
scratch_directory=/work/scratch-nompiio/$(whoami)
if [ ! -d $scratch_directory ]
then
  echo "Creating user $(whoami) scratch directory $scratch_directory"
  mkdir $scratch_directory
else
  echo "Scratch directory is $scratch_directory"
fi
