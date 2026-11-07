#!/bin/sh
# Build the WPE offscreen spike inside the aarch64 build VM.
#
# The binary links against the *device's* libWPEWebKit/libwpe/WPEBackend-fdo
# (copied by vm-prepare-sysroot.sh) so the ABI it resolves is exactly the one
# installed on the phone. The VM's glibc (2.39) is older than the phone's
# (2.41), so the resulting binary only requires symbols the phone provides.
set -eu
SYSROOT=/var/tmp/sd-webview-spike
SRC=/media/psf/Home/WorkSpace/saidroid-next/native/webview/spike
OUT="$SYSROOT/wpe_offscreen_spike"

[ -d "$SYSROOT/include/wpe-webkit-2.0" ] || { echo "missing sysroot; run vm-prepare-sysroot.sh" >&2; exit 1; }

echo "== compiling"
gcc -O2 -g -Wall -Wextra -Wno-unused-parameter \
    -o "$OUT" "$SRC/wpe_offscreen_spike.c" \
    -I"$SRC/soup-stub" \
    -I"$SYSROOT/include/wpe-webkit-2.0" \
    -I"$SYSROOT/include/wpe-1.0" \
    -I"$SYSROOT/include/wpe-fdo-1.0" \
    $(pkg-config --cflags glib-2.0 gio-2.0 gobject-2.0) \
    -L"$SYSROOT/lib" -Wl,-rpath-link,"$SYSROOT/lib" -Wl,--allow-shlib-undefined \
    -Wl,--no-as-needed \
    -lWPEWebKit-2.0 -lwpe-1.0 -lWPEBackend-fdo-1.0 \
    -lwayland-server -lz \
    $(pkg-config --libs glib-2.0 gio-2.0 gobject-2.0)

echo "== result"
ls -l "$OUT"
sha256sum "$OUT"
echo "== needed"
readelf -d "$OUT" | grep -E "NEEDED|RPATH|RUNPATH|SONAME" || true
echo "== undefined wpe/webkit symbols (must all resolve on the phone)"
nm -D --undefined-only "$OUT" | grep -E "webkit_|wpe_|wl_shm" | head -20 || true
echo "BUILD_OK"
