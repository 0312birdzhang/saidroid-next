#!/bin/bash
set -eu
V=/tmp/sdinput-build
mkdir -p $V
gcc -O2 -Wall -o $V/sdinput /media/psf/Home/WorkSpace/saidroid-next/scripts/input/sdinput.c 2>&1 | head -10
ls -l $V/sdinput
