#!/bin/sh
# Read-only, runs on device. libqtwpe.so (no .1) is the Qt<->WPE integration lib;
# the previous probe looked for libqtwpe.so.1 which does not exist.
Q=/usr/lib64/libqtwpe.so
echo "## $Q size=$(stat -c %s "$Q" 2>/dev/null)"
echo "== NEEDED =="
readelf -d "$Q" 2>&1 | grep NEEDED
echo "== Qt NEEDED count: $(readelf -d "$Q" 2>/dev/null | grep -c libQt5)"
echo "== total exports: $(nm -D --defined-only "$Q" 2>/dev/null | wc -l)"
echo "== exports with wpe/renderer/host/target/export (demangled-ish name grep) =="
nm -D --defined-only "$Q" 2>/dev/null | grep -iE 'wpe|renderer|host|target|export|egl' | head -30
echo "== undefined wpe_renderer_* (who it expects at runtime) =="
nm -D --undefined-only "$Q" 2>/dev/null | grep -iE 'wpe_renderer|wpe_view' | head -20
