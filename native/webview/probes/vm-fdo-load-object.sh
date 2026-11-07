#!/bin/sh
# Compile and run fdo-load-object-probe in the VM (offline, no device needed).
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
SRC=$REPO/native/webview/probes/fdo-load-object-probe.c
OUT=/var/tmp/sd-webview-fdo-probe
SYS=/var/tmp/sd-webview-spike/lib
FDO=$(ls $SYS/libWPEBackend-fdo-* 2>/dev/null | head -1)
mkdir -p "$OUT"
[ -n "$FDO" ] || { echo NO_FDO_LIB; exit 2; }
echo "FDO=$FDO"
gcc -O0 -g -o "$OUT/fdo-load-object-probe" "$SRC" -ldl
echo "BUILD_OK $(ls -l "$OUT/fdo-load-object-probe" | awk '{print $5}')"
LD_LIBRARY_PATH="$SYS:/usr/lib/aarch64-linux-gnu" "$OUT/fdo-load-object-probe" "$FDO"
