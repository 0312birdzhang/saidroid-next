#!/bin/bash
set -euo pipefail
cd /media/psf/Home/WorkSpace/saidroid-next
python3 scripts/perf/build-scroll-apk-vm.py r79-probe4
sha256sum /var/tmp/saidroid-next-api29-perfscroll-r79-probe4/scroll.apk
