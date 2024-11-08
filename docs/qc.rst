.. Marine observations suite documentation master file, created by
   sphinx-quickstart on Thu Jul 23 07:39:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

QualityControl
==============

Between level1d and level1e, please run the MetOffice quality control suite.

The quality control suite consist of three steps:

1. pre-processing: This pre-processing step takes the data from level1d and adds the excluded data from level1a.

.. code-block:: bash
  qc_suite -preproc

Optionally, if date information is given in the file names, please run the command with option --date_avail.

2. standard quality control suite: This is the regular MetOffice QC suite.

.. code-block:: bash
  qc_suite -qc

3. high-resolution quality control suite: This is the high-resolution MetOffice QC suite.

.. code-block:: bash
  qc_suite -hi_qc

After step 1 has passed, step2 and step3 can run in parallel.

For more options run:

.. code-block:: bash
  qc_suite -h
