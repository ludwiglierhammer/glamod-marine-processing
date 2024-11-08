.. Marine observations suite documentation master file, created by
   sphinx-quickstart on Thu Jul 23 07:39:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tool set-up
===========

Code repository
---------------

The full set of suites that make up the marine code are integrated in the
glamod-marine-processing repository. Thus, to install the observations suite,
the repository needs to be cloned:

.. code-block:: bash

  git clone https://github.com/glamod/glamod-marine-processing


Setting paths and environments
------------------------------

The paths for the processing software and data files, including a scratch directory for the user
running the software will be created automatically while calling the software the first time.
Edit the script file and set the environment variables as indicated below:

* code_directory: full path to the obs-suite code.
* home_directory_smf: full path to the obs-suite configuration.
* data_directory: full path to marine data file system.
* scratch_directory: this is system dependent

These paths are pre-defined for KAY, MeluXina and BASTION. The default machine is BASTION.
You can set the paths via the command-line interface.

Installation
------------

To install the minimum dependency version, run:

.. code-block:: bash

  pip install -e .

To install the optional dependencies for the quality control workflow, run:

.. code-block:: bash

  pip install -e .[qc]

To install the optional dependencies for the observations workflow, run:

.. code-block:: bash

  pip install -e .[obs]

To install the all the above for complete dependenciy version, run:

.. code-block:: bash

  pip install -e .[complete]

This will also install all required dependencies.
