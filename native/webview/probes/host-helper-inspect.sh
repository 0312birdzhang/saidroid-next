#!/bin/sh
# Inspect the Sailfish WPE helper launchers (read-only, no device lock needed).
for h in /usr/libexec/wpe-webkit-2.0/WPEWebProcess /usr/libexec/wpe-webkit-2.0/WPENetworkProcess; do
    echo "=== $h"
    readelf -d "$h" 2>/dev/null | grep -E 'NEEDED|RPATH|RUNPATH'
    echo "-- symbols"
    nm -D --undefined-only "$h" 2>/dev/null | awk '{print $NF}' | sed 's/@.*//' | sort -u | head -20
    echo "-- strings of interest"
    strings -a "$h" | grep -vE '^(_|GLIBC|GCC|\.)' | head -30
    echo "-- main?"
    nm -C "$h" 2>/dev/null | grep -E ' main$| T ' | head -10
done
echo "=== does the helper exec something?"
strings -a /usr/libexec/wpe-webkit-2.0/WPEWebProcess | grep -E '/(usr|opt)/' | head -20
echo "=== runtime-common internals: webprocess wrappers"
grep -nE 'WebProcess|NetworkProcess|helper' /opt/wpe-sfos/libexec/atlantic/runtime-common.sh | head -30
