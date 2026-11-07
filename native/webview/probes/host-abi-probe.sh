#!/bin/sh
# host-abi-probe.sh -- read-only survey, RUNS ON THE DEVICE (invoked over ssh by
# vm-host-abi-probe.sh). Deliberately contains no ssh of its own: an earlier version
# of this file had the ssh wrapper baked in and, when executed on the device, tried
# to ssh to itself. A probe script must know which machine it runs on.
#
# Question: is Jolla's renderer host available as a reusable library, so we do not
# have to implement the renderer-host protocol ourselves?
echo "== host libs: ownership + size"
for f in /usr/lib64/libsailfishbrowser.so.1 /usr/lib64/wpe-compat/libegl-stubs.so \
         /usr/lib64/wpe-compat/libsyncskip.so /usr/lib64/wpe-compat/libsigill_skip.so \
         /opt/wpe-sfos/libexec/wpe-webkit-2.0/WPEWebProcess; do
    [ -e "$f" ] || { echo "MISSING $f"; continue; }
    echo "## $f"
    echo "   size=$(stat -c %s "$f" 2>/dev/null) pkg=$(rpm -qf "$f" 2>/dev/null || echo UNKNOWN)"
done
echo "== NEEDED: libsailfishbrowser"
readelf -d /usr/lib64/libsailfishbrowser.so.1 2>/dev/null | grep NEEDED
echo "== Qt NEEDED count in libsailfishbrowser:"
readelf -d /usr/lib64/libsailfishbrowser.so.1 2>/dev/null | grep -c "libQt5" || true
echo "== NEEDED: libegl-stubs"
readelf -d /usr/lib64/wpe-compat/libegl-stubs.so 2>/dev/null | grep NEEDED
echo "== NEEDED: libsyncskip"
readelf -d /usr/lib64/wpe-compat/libsyncskip.so 2>/dev/null | grep NEEDED
echo "== NEEDED: libsigill_skip"
readelf -d /usr/lib64/wpe-compat/libsigill_skip.so 2>/dev/null | grep NEEDED
echo "== flat C exports in libsailfishbrowser matching renderer/egl/wpe/host/export"
nm -D --defined-only /usr/lib64/libsailfishbrowser.so.1 2>/dev/null \
    | grep -iE " (wpe_|egl|.*renderer|.*host|.*export|.*target)" | head -40
echo "== mangled C++ exports mentioning renderer/host/target"
nm -D --defined-only /usr/lib64/libsailfishbrowser.so.1 2>/dev/null \
    | grep -E "renderer|RendererHost|EGLTarget|Exportable" | head -30
echo "== total exported symbols in libsailfishbrowser"
nm -D --defined-only /usr/lib64/libsailfishbrowser.so.1 2>/dev/null | wc -l
echo "== libegl-stubs exports (all)"
nm -D --defined-only /usr/lib64/wpe-compat/libegl-stubs.so 2>/dev/null | head -50
echo "== ldd WPEWebProcess (full)"
ldd /opt/wpe-sfos/libexec/wpe-webkit-2.0/WPEWebProcess 2>&1
