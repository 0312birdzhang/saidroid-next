#!/bin/bash
# Marker check: the component must be r78's tree plus the direct-copy change only.
set -euo pipefail
cd /media/psf/Home/WorkSpace/saidroid-next
OUT=/var/tmp/saidroid-next-api29-product-r79
TMP=$(mktemp -d)
cd "$TMP"
unzip -oq "$OUT/runtime.jar" classes.dex
python3 - "$TMP/classes.dex" "$OUT/libsdwindow.so" <<'PY'
import sys
dex = open(sys.argv[1], 'rb').read()
so = open(sys.argv[2], 'rb').read()
def count(hay, needle):
    n, i = 0, 0
    while True:
        i = hay.find(needle, i)
        if i < 0: return n
        n += 1; i += 1
print('DEX_BYTES', len(dex))
for name in (b'SDVIEWS', b'ERROR_NO_RENDERER', b'SAILDROID_DIRECT_COPY',
             b'SDWebViewProvider', b'SAILDROID_PERF'):
    print('DEX_COUNT', name.decode(), count(dex, name))
print('SO_BYTES', len(so))
for name in (b'SAILDROID_DIRECT_COPY', b'SAILDROID_DIRECT_SHM', b'SAILDROID_PERF',
             b'SDNATIVE', b'ABGR'):
    print('SO_COUNT', name.decode(), count(so, name))
PY
