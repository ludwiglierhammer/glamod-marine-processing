home_directory=/group_workspaces/jasmin2/glamod_marine
data_directory=$home_directory/data

home_directory_smf=/gws/smf/j04/c3s311a_lot2
code_repo_directory=$home_directory_smf/code/marine_code/glamod-marine-processing_ipg
pyTools_directory=$code_repo_directory/obs-suite/modules/python
um_code_directory=$code_repo_directory/user-manual
data_directory=$home_directory/data

echo 'Data directory is '$data_directory
echo 'User manual code directory is '$um_code_directory

# Create the scratch directory for the user
scratch_directory=/work/scratch-nompiio/$(whoami)
if [ ! -d $scratch_directory ]
then
  echo "Creating user $(whoami) scratch directory $scratch_directory"
  mkdir $scratch_directory
else
  echo "Scratch directory is $scratch_directory"
fi
