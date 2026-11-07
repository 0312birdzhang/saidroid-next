#!/bin/bash
set -e
cd /media/psf/Home/WorkSpace/saidroid-next
python3 scripts/perf/build-perf-release-vm.py perf7 2>&1 | tail -30
