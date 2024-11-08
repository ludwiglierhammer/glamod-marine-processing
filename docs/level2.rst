.. Marine observations suite documentation master file, created by
   sphinx-quickstart on Thu Jul 23 07:39:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Level 2
========

After visual inspection of the reports generated in level1e, only observation
tables reaching a minimum quality standard proceed to level2: this might imply
rejecting a full sid-dck dataset or an observational table or change the period
of data to release. The level1e data composition that has been used to generate
the level2 product of every release is configured in level2.json file available
in the release configuration directory. Prior to first use this file needs to be
created.

This script creates the selection file level2.json in the execution directory.
The parameters year_init and year_end are used to set the final period of data
release, that might be different to that initially processed. The data period of
each of the individual source-deck data partitions is adjusted in the level2.json
file according to these arguments.

After checking data quality on the level1e
reports, edit the data selection file as needed to create the final dataset
composition:

*	Remove a full sid-dck from level2 by setting to true the sid-dck ‘exclude’ tag.
*	Remove an observation table from the full dataset by adding it to the list under the general ‘params_exclude’ tag.
*	Remove an observation table from a sid-dck by adding it to the list under the sid-dck ‘params_exclude’ tag.
*	Adjust the release period of a sid-dck by modifying the ‘year_init|end’ tags of the sid-dck
*	Observation tables to be removed have to be named as observations-[at|sst|dpt|wbt|wd|ws|slp]
*	All edits need to be consistent with JSON formatting rules.

Once file level2.json has been edited the file needs to be copied to its
directory in the configuration repository to be version controlled.

In the file sample below, all observations-wbt table files will be retained for
level2, while observations-at will be dropped from level2 only in source-deck
063-714.

.. literalinclude:: config_files/level2.json

This script executes a job per source and deck included in the process_list.
The configuration file for the process (level2.json) is directly accessed from
the release configuration directory.

This script logs to *data_dir*/release/dataset/level2/log/sid-dck/. Log files
are *sid-dck*-*release*-*update*.ext with ext either ok or failed depending on the
subjob termination status.

List  \*.failed in the sid-dck level2 log directories to find if any went wrong.
