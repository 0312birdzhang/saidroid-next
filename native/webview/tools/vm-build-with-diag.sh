#!/bin/sh
# Build an isolated product image that contains the draw-audit provider.
# OUTPUT_DIR must match /var/tmp/saidroid-next-* (build script enforces it).
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT=/var/tmp/saidroid-next-webview-diag
rm -rf "$OUT"
OUTPUT_DIR="$OUT" /bin/bash "$REPO/scripts/build-activity-manager.sh" 2>&1 | tail -40
echo "BUILD_OUT=$OUT"
ls -la "$OUT" | head -20
