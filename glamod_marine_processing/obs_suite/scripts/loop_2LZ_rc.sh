#!/bin/bash
for sid in $1
    do
    for y in 2022
        #{2021..2022..1}
        do
        for m in {01..12..1}
            do
            echo "$y" "$m" "$sid"
            python3 level2_applylz_rc.py -l2path /ichec/work/glamod/data/marine/release_6.0/ICOADS_R3.0.2T/level2/ -lzpath /ichec/work/glamod/data/marine/release_6.0/LZ_UIDS/ -release release_6.0 -update 000000 -sid_dck $sid -year $y -month $m
            done
        done
    done
