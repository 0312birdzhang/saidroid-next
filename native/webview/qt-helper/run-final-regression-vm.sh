#!/bin/bash
set -euo pipefail
repo=/media/psf/Home/WorkSpace/saidroid-next
cd "$repo"
bash native/webview/qt-helper/run-perf-regression-vm.sh api29-r84-webview-20261029-3 perf-r84-20261029
