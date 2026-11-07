#!/bin/sh
LIB=/var/tmp/sd-webview-spike/lib
FDO=$LIB/libWPEBackend-fdo-1.0.so.1.11.0
echo "== strings in fdo matching _wpe_ =="
strings -a "$FDO" | grep -n '_wpe_' | head -40
echo "== count: $(strings -a "$FDO" | grep -c '_wpe_')"
echo "== all dynamic exports of fdo (defined) =="
nm -D --defined-only "$FDO" 2>/dev/null | awk '{print $2, $3}' | sort | head -40
echo "== fdo dependencies (NEEDED) =="
readelf -d "$FDO" 2>/dev/null | grep NEEDED
echo "== does fdo dlopen anything? (DT_NEEDED + strings .so) =="
strings -a "$FDO" | grep -E '\.so(\.|$)' | sort -u | head -20
