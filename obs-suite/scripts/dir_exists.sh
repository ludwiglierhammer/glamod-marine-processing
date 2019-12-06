#!/bin/bash
#
# Usage: ./dir_exists dir_path


if [ -d $1 ]
then
 exit 0
else
 exit 1
fi
