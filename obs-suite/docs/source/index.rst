.. Marine observations suite documentation master file, created by
   sphinx-quickstart on Thu Jul 23 07:39:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Marine observations suite's documentation!
=====================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Introduction (complete)
=======================

Tool set-up (review)
====================

Code set up
-----------

Clone the remote repository:

.. code-block:: bash

  git clone git@git.noc.ac.uk:iregon/marine-user-guide.git

Build the python environment using the requirements.txt file in marine-user-guide/env. This
step system dependent. The following code block described the steps to
follow in CEDA JASMIN, using the Jaspy toolkit.

.. code-block:: bash

  cd marine-user-guide/env
  module load jaspy/3.7
  virtualenv -–system-site-packages mug_env
  source mug_env/bin/activate
  pip install -r requirements.txt


Initializing a new data release
===============================

Common paths
------------

* *obs-suite*: path of the observations suite in the marine processing repository
* *config_dir*: path to the obs-suite directory in the configuration repository
* *data_dir*: path to general data directory in the marine file system

Create the configuration files for the release and dataset
----------------------------------------------------------

Every data release is identified in the file system with the following tags:

* release: release name (eg. release_2.0)
* update: udpate tag
* dataset: dataset name (eg. ICOADS_R3.0.0T)

Create a new directory *release*-*update*/*dataset*/ in the obs-suite configuration directory (*config_dir*)
of the configuration repository. We will now refer to this directory as *release_config_dir*.

Release periods file
^^^^^^^^^^^^^^^^^^^^

Create file *release_config_dir*/source_deck_periods.json

This file is a json file with each of the source-deck partitions to be included
in the release, and its associated periods (year resolution) to process.

A sample of this file can be found in the appendix: :ref:`periods_file`


Process list file
^^^^^^^^^^^^^^^^^

Create file *release_config_dir*/source_deck_list.txt

This is a simple ascii file with the list of source-deck partitions to process.
Create the master list with the keys of file source_deck_periods.json. This file
can later be subsetted if a given process is to be run in batches.

A sample of this file can be found in the appendix: :ref:`process_list_file`


Set up the release data directory
---------------------------------

Every new release or new dataset in a release needs to have its corresponding
directory structure initialised in the file system:


.. code-block:: bash

  cd obs-suite
  source setpaths.sh
  source setenv0.sh
  cd scripts
  python make_release_source_tree.py data_dir config_dir release update dataset

where:

* release: release identifier in file system
* update: release update identifier in file system
* dataset: dataset identifier in file system


This script does not overwrite existing directories and is safe to run on an existing directory structure.


Level 1a
========

.. code:: bash

  cd obs-suite
  source setpaths.sh
  source setenv0.sh
  cd lotus_scripts
  python level1a_slurm.py release udpate dataset config_path process_list failed_only

where:

* release: release identifier in file system
* update: release update identifier in file system
* dataset: dataset identifier in file system
* config_path: path to obs-suite configuration directory
* process_list: filename in *config_path*/*release*/*dataset* with the list of partitions to process
* failed_only: optional (yes/no). Defaults to no


Appendix. Configuration files
=============================

.. _periods_file:

Release periods file
--------------------

.. literalinclude:: ../config_files/source_deck_periods.json


.. _process_list_file:

Process list file
-----------------

.. literalinclude:: ../config_files/source_deck_list.txt
