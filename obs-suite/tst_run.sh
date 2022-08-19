#!/bin/bash
on the code environment:
cd /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite
virtualenv --system-site-packages env3
source env3/bin/activate
pip install -r requirements_env2.txt
source setpaths_sb.sh
source setenv3.sh

# mk subdirectories
python3 scripts/make_release_source_tree.py /gws/nopw/j04/glamod_marine/data/ /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ release_5.0 000000 ICOADS_R3.0.2T_NRT

# until disk quota exceeded is resolved made:
python3 scripts/make_release_source_tree.py /gws/nopw/j04/c3s311a_lot2/data/marine /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ release_5.0 000000 ICOADS_R3.0.2T_NRT

#once resolved change setpaths_sb.sh back to the normal data path


# run pre-processing
add paths to config.json and run main.py

# process level1a for one file
python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-792 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-793 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-794 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-795 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-797 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-992 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-993 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-994 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-995 2015 01 IMMA1_R3.0.2T_NRT_2015-01

python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 172-798 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# level1a
# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-792 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# tmp data directory
python3 scripts/level1a_sb.py /gws/nopw/j04/c3s311a_lot2/data/marine/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-792 2015 02 IMMA1_R3.0.2T_NRT_2015-02


# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-793 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-794 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-795 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 103-797 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-992 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-993 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-994 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 114-995 2015 01 IMMA1_R3.0.2T_NRT_2015-01

# python3 scripts/level1a_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1a.json 172-798 2015 01 IMMA1_R3.0.2T_NRT_2015-01

#gunzip -c /gws/nopw/j04/glamod_marine/data/release_5.0/NOC_corrections/v1x2022/duplicates/2015-01.txt.gz > /gws/nopw/j04/glamod_marine/data/release_5.0/NOC_corrections/v1x2022/duplicates/2015-01.txt
#nedit /gws/nopw/j04/glamod_marine/data/release_5.0/NOC_corrections/v1x2022/duplicates/2015-01.txt &

# level1b
#python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 103-792 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 103-793 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 103-794 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 103-795 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 103-797 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 114-992 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 114-993 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 114-994 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 114-995 2015 01

python3 scripts/level1b_sb.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1b.json 172-798 2015 01

# level1c
# python3 scripts/level1c.py /gws/nopw/j04/glamod_marine/data/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1c.json 103-792 2015 01
python3 scripts/level1c.py /gws/nopw/j04/c3s311a_lot2/data/marine/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1c.json 103-793 2015 01

# level1d
python3 scripts/level1d_sb.py /gws/nopw/j04/c3s311a_lot2/data/marine/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1d.json 114-992 2015 01

# level1e
python3 scripts/level1e.py /gws/nopw/j04/c3s311a_lot2/data/marine/ release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/level1e.json 103-792 2015 02


# lotus scripts
# level1a
python3 lotus_scripts/level1a_slurm_sb.py release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_list.txt

# level1b
python3 lotus_scripts/level1b_slurm_sb.py release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_list.txt

# level1c
python3 lotus_scripts/level1c_slurm_sb.py release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_list.txt

# level1d
python3 lotus_scripts/level1d_slurm_sb.py release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_list.txt

# preprocess_qc
python3 ../qc-suite/scripts/preprocess_rc2.py -source /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/ICOADS_R3.0.2T_NRT/level1d -dck_list /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_list.txt -dck_period /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_periods.json -corrections /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/NOC_corrections/v1x2022 -destination /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/metoffice_qc/base
 
# process qc suite    
cd /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/metoffice_qc
mkdir /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/metoffice_qc/logs_qc/
mkdir /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/metoffice_qc/logs_qc/successful
mkdir /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/metoffice_qc/logs_qc/failed

sbatch /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/lotus_scripts/submit_qc_slurm.sh

python3 /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/scripts/marine_qc_sb.py -jobs /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/config/jobs2_sb.json -job_index 84 -config /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/config/configuration_r3.0.2.txt -tracking

sbatch /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/qc-suite/lotus_scripts/submit_qc_hr_slurm.sh

# level1e
python3 lotus_scripts/level1e_slurm.py release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_list.txt

# level2
python3 lotus_scripts/level2_slurm.py release_5.0 000000 ICOADS_R3.0.2T_NRT /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/ /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-processing/obs-suite/configuration_files/release_5.0-000000/ICOADS_R3.0.2T_NRT/source_deck_list.txt

# repeat qc for files 2014-12 & 2022-01

# mug
cd /gws/smf/j04/c3s311a_lot2/code/marine_code/marine-user-guide/
source setpaths_sb.sh
source setenv.sh

# modified
/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/mug_init_input.json
/gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/mug_list.txt_v8

python3 /gws/smf/j04/c3s311a_lot2/code/marine_code/marine-user-guide/init_version/init_config.py 
#when prompted added:
Input filename and path for output: /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/mug_config_v8.json

python3 /gws/smf/j04/c3s311a_lot2/code/marine_code/marine-user-guide/init_version/create_version_dir_tree.py /gws/nopw/j04/c3s311a_lot2/data/marine/mug v8 /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/mug_config_v8.json

cd init_version
./merge_release_data_sb.slurm v8 /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/mug_config_v8.json /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/mug_list.txt_v8

./merge_release_data_check_sb.sh  (not correct)

cd ../data_summaries
./monthly_grids.slurm v8 /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/monthly_grids_sb.json


./monthly_qi_sb.slurm v8 /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/monthly_qi.json

cd ../figures
python3 nreports_ts_plot_sb.py /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/nreports_ts_plot.json
 
python3 duplicate_status_ts_plot.py /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/duplicate_status_ts_plot.json

python3 report_quality_ts_plot_sb.py /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/report_quality_ts_plot.json

python3 nreports_hovmoller_plot_sb.py /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/nreports_hovmoller_plot.json (not working)

python3 ecv_coverage_ts_plot_grid_sb.py /gws/smf/j04/c3s311a_lot2/code/marine_code/glamod-marine-config/marine-user-guide/v8/ecv_coverage_ts_plot_grid.json
