home_directory=/group_workspaces/jasmin2/glamod_marine
home_directory_smf=/gws/smf/j04/c3s311a_lot2
code_directory=$home_directory_smf/code/marine_code/glamod-marine-processing_ipg/obs-suite
pyTools_directory=$code_directory/modules/python
scripts_directory=$code_directory/scripts
data_directory=$home_directory/data

echo 'Data directory is '$data_directory
echo 'Code directory is '$code_directory

# Create the scratch directory for the user
scratch_directory=/work/scratch-nopw/$(whoami)
if [ ! -d $scratch_directory ]
then
  echo "Creating user $(whoami) scratch directory $scratch_directory"
  mkdir $scratch_directory
else
  echo "Scratch directory is $scratch_directory"
fi
