#!/bin/bash
set -e
cd /media/psf/Home/WorkSpace/saidroid-next
rm -rf /var/tmp/saidroid-next-api29-perfscroll-perf7
python3 scripts/perf/build-scroll-apk-vm.py perf7 2>&1 | tail -20
