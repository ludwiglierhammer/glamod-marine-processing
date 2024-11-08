.. Marine observations suite documentation master file, created by
   sphinx-quickstart on Thu Jul 23 07:39:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   
Post-processing of level1a data
===============================

After performing your level1a suite, you can put your decks together into one new deck. See:

.. code-block:: bash
  post_proc
  
Optionally, if date information is given in the file names, please run the command with option --date_avail.

Old deck list:

.. literalinclude:: config_files/source_deck_list.txt

New deck list:

.. literalinclude:: config_files/source_deck_list_post.txt

For more details run:

.. code-block:: bash
  post_proc -h