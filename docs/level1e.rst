.. Marine observations suite documentation master file, created by
   sphinx-quickstart on Thu Jul 23 07:39:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Level 1e
========

The level1e processing merges the data quality flags from the Met Office QC
suite (add ref) with the data from level 1d. The QC software generates two sets
of QC files, one basic QC of the observations from all platforms and an enhanced
track and quality check for drifting buoy data. The basic QC flags are stored in
*data_directory*/*release*/*dataset*/metoffice_qc/base/.

This script executes an array of monthly subjobs per source and deck included in
the process_list. The configuration for the process is directly accessed from
the release configuration directory: the data period processed is as configured
per source and deck in the release periods file ( :ref:`release_periods_file`)
and the level1e configuration is retrieved from :ref:`level1e_config_file`.

For more details run:

.. code-block:: bash

  obs_suite -h

This script logs to *data_dir*/release/dataset/level1e/log/sid-dck/. Log files
are yyyy-mm-<release>-<update>.ext with ext either ok or failed depending on the
subjob termination status.

List  \*.failed in the sid-dck level1e log directories to find if any went wrong.

After the basic QC flags have been merged the enhanced drifting buoy flags need
to be merged with the level1e data. This process is described under Quality
control in 4.4.6 in the C3S Technical Service Document (but will be moved to the level1e
processing in a future update).

Once the drifting buoy flags have been merged the data files will no longer
change and summary data reports need to be generated prior to the data moving to
level2. See documentation in git@git.noc.ac.uk:iregon/marine-user-guide.git to
create the reports.
