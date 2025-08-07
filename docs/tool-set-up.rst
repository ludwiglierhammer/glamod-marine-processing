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

Once you have a copy of the source, you can install it with pip_:

.. code-block:: console

   pip install -e .

If you're interested in participating in the development of the **glamod-marine-processing**, you can install the package in development mode after cloning the repository from source:

.. code-block:: console

    pip install -e .[dev]      # Install optional development dependencies in addition
    pip install -e .[docs]     # Install optional dependencies for the documentation in addition
    pip install -e .[all]      # Install all the above for complete dependency version
