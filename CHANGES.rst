
=========
Changelog
=========

v7.0.1 (unpublished)
--------------------
Contributors to this version: Ludwig Lierhammer (:user:`ludwiglierhammer`)

Announcements
^^^^^^^^^^^^^
* make preparations for zenodo DOI assignment (:pull:`42`)
* adding readthedocs documentation (:pull:`42`)
 Now under Apache v2.0 license (:pull:`42`)

New features and enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* add quality checks for both Wind speed and wind direction in level1e script (:issue:`20`, :pull:`22`)
* add pre-processing for ICOADS data (:pull:`24`)
* add post processing for C-RAID level1a data (:pull:`26`)
* ``obs_suite``: optionally, set list of decks to process (:pul:`25`)
* ``obs_suite``: optionally, set both release period init and end year (:pull:`25`)
* ``obs_suite``: configuration files for C-RAID (:pull:`25`)
* ``obs_suite``: running with C-RAID data (:pull:`25`)
* ``obs_suite`` and ``qc_suite``: optionally, run jobs in parallel with gnu_parallel (:pull:`41`)

Breaking changes
^^^^^^^^^^^^^^^^
* delete metadata suite, config suite and not-used scripts/modules (:issue:`14`, :pull:`16`)
* adjust ``obs_suite`` to ``cdm_reader_mapper`` version ``v0.4.0`` (yet unpublished) (:pull:`21`)
* ``obs_suite``: date information is NOT mandatory in filenames anymore (:pull:`25`)
* ``obs_suite``: pass tables if no correction or quality control file are available (:pull:`25`)
* ``obs_suite``: adjust both process deck lists and processing init/end years to release7.0 requirements (:pull:`27`)
* ``obs_suite``: adjust structure to ``cdm_reader_mapper`` structure (:pull:`28`)
* ``qc_suite``: no need for NOC correction files (:pull:`39`)
* ``obs_suite``: new ICOADS_R3.0.2T deck list after level 1a (:pull:`40`)
* ``obs_suite``: starting with year 2014 (:pull:`40`)
* set BASTION do default machine_ bastion01.core.ichec.ie (:pull:`37`)
* ``obs_suite``: use duplicate checker from ``cdm_reader_mapper`` instead of NOc correction files in level1b (:pull:`37`)


Bug fixes
^^^^^^^^^
* fixing observation suite level1e tests (:pull:`17`)
* level1e: changed QC mapping from ``v7.0.0`` is now running by setting values of ``location_quality`` and ``report_time_quality`` to ``str`` (:pull:`18`)
* level1c: use only observation reports that are also available in the header file (:pull:`44`)

v7.0.0 (2024-06-13)
-------------------
Contributors to this version: Ludwig Lierhammer (:user:`ludwiglierhammer`)

Announcements
^^^^^^^^^^^^^^
renaming release name to vX.Y.Z

release_7.0.0 (2024-06-13)
--------------------------
Contributors to this version: Ludwig Lierhammer (:user:`ludwiglierhammer`)

Breaking changes
^^^^^^^^^^^^^^^^
* delete empty and not used files, functions and folders (:pull:`3`)
* create requirements for each suite (:pull:`3`)
* rebuild to a installable python package (:pull:`3`)
* install package and requirements via a pyproject.toml file (:pul::`3`)
* change QC mapping in obs_suite level1e (:issue:`7`, :pull:`8`):

  * if ``location_quality`` is equal ``2`` set both ``report_quality`` and ``quality_flag`` to ``1``
  * if ``report_time_quality`` is equal ``4`` or ``5`` set both ``report_quality`` and ``quality_flag`` to ``1``

New features and enhancements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* add some information files: ``AUTHORS.rst``, ``CHANGES.rst``, ``CONTRIBUTING.rst`` and ``LICENSE`` (:pull:`3`)
* make us of pre-commit (:pull:`3`)
* make use of an command-line interface to create suite PYTHON and SLURM scripts (:pull:`3`, :pull:`5`)
* add new release 7.0 configuration files (:pull:`3`)
* set some default directories and SLURM settings for both HPC systems KAY and MeluXina (:pull:`3`)

Internal changes
^^^^^^^^^^^^^^^^
* reduce complexity of some functions (:pull:`3`)
* adding observational testing suite (:issue:`5`, :pull:`5`)
* load data from ``cdm-testdata`` (:pull:`11`)
