==================================================================
GLAMOD marine processing: ``glamod-marine-processing`` toolbox
==================================================================

+----------------------------+-----------------------------------------------------+
| Versions                   | |tag| |release|                                     |
+----------------------------+-----------------------------------------------------+
| Documentation and Support  | |docs|                                              |
+----------------------------+-----------------------------------------------------+
| Open Source                | |license| |zenodo|                                  |
+----------------------------+-----------------------------------------------------+
| Coding Standards           | |black| |ruff| |pre-commit| |fossa| |codefactor|    |
+----------------------------+-----------------------------------------------------+
| Development Status         | |status| |build| |coveralls|                        |
+----------------------------+-----------------------------------------------------+
| Funding                    | |funding| |noc|                                     |
+----------------------------+-----------------------------------------------------+

``glamod-marine-processing`` is a python tool for creating SLURM scripts for several GLAMOD marine processing workflows.
Once installed you can use it as an command-line interface. For more information, please call the help functions:

.. code-block:: console

    qc_suite --help        # Quality control workflow help page
    obs_suite --help       # Observations workflow help page

Installation
------------
Before you install ``glamod-marine-processing`` please clone the GitHub repository.

.. code-block:: console

    git clone https://github.com/glamod/glamod-marine-processing
    cd glamod-marine-processing

Now you can install several dependency versions:

.. code-block:: console

    pip install -e .           # Install minimum dependency version
    pip install -e .[qc]       # Install optional dependencies for the quality control workflow
    pip install -e .[obs]      # Install optional dependencies for the observations workflow
    pip install -e .[complete]  # Install all the above for complete dependency version

This will install the package but you can still edit it and you don't need the package in your :code:`PYTHONPATH`.

Documentation
-------------

The official documentation is at https://glamod-marine-processing.readthedocs.io/

Contributing to cdm_reader_mapper
---------------------------------

If you're interested in participating in the development of `glamod-arine-processing` by suggesting new features, new indices or report bugs, please leave us a message on the `issue tracker`_.

If you would like to contribute code or documentation (which is greatly appreciated!), check out the `Contributing Guidelines`_ before you begin!

Credits
-------

``glamod-marine-processing`` development is funded through Copernicus Climate Change Service (C3S_).

Furthermore, acknowledgments go to National Oceanography Centre (NOC_).

.. _C3S: https://climate.copernicus.eu/

.. _Contributing Guidelines: https://github.com/glamod/glamod-marine-processing/blob/main/CONTRIBUTING.rst

.. _issue tracker: https://github.com/glamod/glamod-marine-processing/issues

.. _NOC: https://noc.ac.uk/

.. |build| image:: https://github.com/glamod/glamod-marine-processing/actions/workflows/ci.yml/badge.svg
        :target: https://github.com/glamod/glamod-marine-processing/actions/workflows/ci.yml
        :alt: Build Status

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
        :target: https://github.com/psf/black
        :alt: Python Black

.. |codefactor| image:: https://www.codefactor.io/repository/github/glamod/glamod-marine-processing/badge
		:target: https://www.codefactor.io/repository/github/glamod/glamod-marine-processing
		:alt: CodeFactor

.. |coveralls| image:: https://codecov.io/gh/glamod/glamod-marine-processing/graph/badge.svg
	      :target: https://codecov.io/gh/glamod/glamod-marine-processing
	      :alt: Coveralls

.. |docs| image:: https://readthedocs.org/projects/glamod_marine_processing/badge/?version=latest
        :target: https://glamod-marine-processing.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

.. |fossa| image:: https://app.fossa.com/api/projects/git%2Bgithub.com%2Fglamod%2Fglamod-marine-processing.svg?type=shield
        :target: https://app.fossa.com/projects/git%2Bgithub.com%2Fglamod%2Fglamod-marine-processing?ref=badge_shield
        :alt: FOSSA

.. |funding| image:: https://img.shields.io/badge/Powered%20by-Copernicus-blue.svg
        :target: https://climate.copernicus.eu/
        :alt: Funding

.. |license| image:: https://img.shields.io/github/license/glamod/glamod-marine-processing.svg
        :target: https://github.com/glamod/glamod-marine-processing/blob/main/LICENSE
        :alt: License

.. |noc| image:: https://img.shields.io/badge/Thanks%20to-NOC-blue.svg
        :target: https://noc.ac.uk/
        :alt: NOC

.. |pre-commit| image:: https://results.pre-commit.ci/badge/github/glamod/glamod-marine-processing/master.svg
   :target: https://results.pre-commit.ci/latest/github/glamod/glamod-marine-processing/master
   :alt: pre-commit.ci status

.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
        :target: https://github.com/astral-sh/ruff
        :alt: Ruff

.. |status| image:: https://www.repostatus.org/badges/latest/wip.svg
        :target: https://www.repostatus.org/#wip
        :alt: Project Status: WIP: Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.

.. |release| image:: https://img.shields.io/github/v/release/glamod/glamod-marine-processing.svg
        :target: https://github.com/glamod/glamod-marine-processing/releases
        :alt: Release

.. |tag| image:: https://img.shields.io/github/v/tag/glamod/glamod-marine-processing.svg
        :target: https://github.com/glamod/glamod-marine-processing/tags
        :alt: Tag

.. |zenodo| image:: https://img.shields.io/badge/zenodo-package_or_version_not_found-red
        :target: https://zenodo.org/glamod-marine-processing
 	      :alt: DOI
