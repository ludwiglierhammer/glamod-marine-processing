
=========
Changelog
=========

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
* delete emtpy and not used files, functions and folders (:pull:`3`)
* create requirements for each suite (:pull:`3`)
* rebuild to a installable python package (:pull:`3`)
* install package and requirements via a pyproject.toml file (:pul::`3`)
* change QC mapping in obs_suite level1e (:issue:`7`, :pull:`8`):

  * if ``location_quality`` is equal ``2`` set both ``report_quality`` and ``quality_flag`` to ``1``
  * if ```report_time_quality`` is equal ``4`` or ``5`` set both ``report_quality`` and ``quality_flag`` to ``1``

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
