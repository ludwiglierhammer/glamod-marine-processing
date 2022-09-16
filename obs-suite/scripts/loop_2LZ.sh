#!/bin/bash
for sid in 103-792
    do
    for y in {2015..2021..1}
        do
        for m in {01..12..1}
            do
            echo "$y" "$m" "$sid"
            python3 scripts/level2_applyLZ.py -l2path /gws/nopw/j04/c3s311a_lot2/data/marine/release_5.0/ICOADS_R3.0.2T_NRT/level2/ -lzpath /gws/nopw/j04/c3s311a_lot2/data/marine/ -release release_5.0 -update 000000 -sid_dck $sid -year $y -month $m    
            done
        done
    done

