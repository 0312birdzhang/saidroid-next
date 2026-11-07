#!/bin/sh
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-headers"
mkdir -p "$OUT"
cd /
/usr/bin/python3 /media/psf/Home/WorkSpace/saidroid-next/native/webview/probes/strings-render-dev.py > "$OUT/render-device-strings.txt" 2>&1 || true
echo WROTE
