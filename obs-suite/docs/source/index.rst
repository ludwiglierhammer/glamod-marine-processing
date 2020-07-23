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
* *config_directory*: path to the obs-suite directory in the configuration repository
* *data_directory*: path to general data directory in the marine file system
* *release_config_dir*: full path to the configuration of a specific data release
  within *config_directory*


Create the configuration files for the release and dataset
----------------------------------------------------------

Every data release is identified in the file system with the following tags:

* release: release name (eg. release_2.0)
* update: udpate tag
* dataset: dataset name (eg. ICOADS_R3.0.0T)

Create a new directory *release*-*update*/*dataset*/ in the obs-suite configuration directory (*config_directory*)
of the configuration repository. We will now refer to this directory as *release_config_dir*.

Release periods file
^^^^^^^^^^^^^^^^^^^^

Create file *release_config_dir*/source_deck_periods.json

This file is a json file with each of the source-deck partitions to be included
in the release, and its associated periods (year resolution) to process.

The figure below shows a sample of this file:

.. literalinclude:: ../config_files/source_deck_periods.json


Process list file
^^^^^^^^^^^^^^^^^

Create file *release_config_dir*/source_deck_list.txt

This is a simple ascii file with the list of source-deck partitions to process.
Create the master list with the keys of file source_deck_periods.json. This file
can later be subsetted if a given process is to be run in batches.

The figure below shows a sample of this file:

.. literalinclude:: ../config_files/source_deck_list.txt


Level 1a configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create file *release_config_dir*/level1a.json. This file includes information on
the input files data model, filters used to select reports and the mapping to
apply convert the data to the CDM.

The figure below shows a sample of this file:

.. literalinclude:: ../config_files/level1a.json

This file has its default configuration in the outer keys, with source-deck
specific configuration under the *sid-dck* keys. In the sample given, all the
source and decks will be processed with the default configuration, but 063-714,
that will use its own parameters.

Configuration parameters job* are only used by the slurm launchers, while the
rest by the corresponding level1a.py script.


Set up the release data directory
---------------------------------

Every new release or new dataset in a release needs to have its corresponding
directory structure initialised in the file system:


.. code-block:: bash

  cd obs-suite
  source setpaths.sh
  source setenv0.sh
  cd scripts
  python make_release_source_tree.py $data_directory $config_directory release update dataset

where:

* release: release identifier in file system
* update: release update identifier in file system
* dataset: dataset identifier in file system


This script does not overwrite existing directories and is safe to run on an
existing directory structure if new source-decks have to be added.


Level 1a
========

Level 1a contains the initial data converted from the input data sources
(level0) to files compatible with the CDM.

Every monthly file of the individual source-deck ICOADS dataset partitions is
converted with the following command:

.. code:: bash

  cd obs-suite
  source setpaths.sh
  source setenv0.sh
  cd scripts
  python level1a.py $data_directory release update dataset release_config_dir/level1a.json sid-dck year month

where:

* release: release identifier in file system
* update: release update identifier in file system
* dataset: dataset identifier in file system
* sid-dck: source-deck identifier
* year: file year, format yyyy
* month: file month, format mm


To facilitate the processing of a large number of files level1a.py can be run
in batch mode:

.. code:: bash

  cd obs-suite
  source setpaths.sh
  source setenv0.sh
  cd lotus_scripts
  python level1a_slurm.py release update dataset $config_directory process_list failed_only

where:

* release: release identifier in file system
* update: release update identifier in file system
* dataset: dataset identifier in file system
* process_list: filename in *release_config_dir* with the list of partitions to process
* failed_only: optional (yes/no). Defaults to no
