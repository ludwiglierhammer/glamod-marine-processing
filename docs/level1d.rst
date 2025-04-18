.. Marine observations suite documentation master file, created by
   sphinx-quickstart on Thu Jul 23 07:39:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Level 1d
========

The level1d files contain the level1c data merged with external metadata (where
available). In the current marine processing implementation, the level1c are
merged with WMO Publication 47 metadata to set instrument heights, station names
and platform sub types (i.e. type of ship). Prior to merging, the WMO
Publication 47 metadata are harmonised, quality controlled and pre-processed in
a process that run independently to this data flow (add ref). After
pre-processing, this info needs to be made available to the release in directory
*data_directory*/*release*/wmo_publication_47/monthly/.

For more details run:

.. code-block:: bash

  obs_suite -h

This script executes an array of monthly subjobs per source and deck included in
the process_list. The configuration for the process is directly accessed from
the release configuration directory: the data period processed is as configured
per source and deck in the release periods file ( :ref:`release_periods_file`)
and the level1d configuration is retrieved from :ref:`level1d_config_file`.

This script logs to *data_dir*/release/dataset/level1d/log/sid-dck/. Log files
are yyyy-mm-<release>-<update>.ext with ext either ok or failed depending on the
subjob termination status.

List  \*.failed in the sid-dck level1e log directories to find if any went wrong.
