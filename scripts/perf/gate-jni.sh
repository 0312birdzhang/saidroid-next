#!/bin/bash
# Run the build-time JNI contract gate inside the build VM.
#   scripts/perf/gate-jni.sh [path/to/libsdwindow.so]
# Exit 3 + BUILD_RC=refused_field_mismatch means: do not build.
set -u
cd /media/psf/Home/WorkSpace/saidroid-next
exec python3 scripts/perf/check-jni-contract.py ${1:+--so "$1"}
