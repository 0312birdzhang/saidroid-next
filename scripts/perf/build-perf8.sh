#!/bin/bash
set -e
cd /media/psf/Home/WorkSpace/saidroid-next
python3 scripts/perf/build-perf-release-vm.py perf8 2>&1 | tail -8
