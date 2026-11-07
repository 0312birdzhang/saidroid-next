#!/bin/bash
set -e
cd /media/psf/Home/WorkSpace/saidroid-next
python3 scripts/perf/build-perf-release-vm.py perf9 --from-product /var/tmp/saidroid-next-api29-product-perf-perf8 2>&1 | tail -8
