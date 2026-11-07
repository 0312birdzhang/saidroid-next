#!/bin/sh
# Read-only: find the WPE *backend* library Atlantic/WebKit actually loads on this
# device (the piece that owns the renderer-host + hybris native window path).
set -u
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"

echo "== /opt/wpe-sfos tree (files only, depth 3)"
$SSH 'find /opt/wpe-sfos -maxdepth 3 -type f -o -maxdepth 3 -type l 2>/dev/null | sort'

echo
echo "== candidate backend libs anywhere on device"
$SSH 'ls -l /usr/lib64/libWPEBackend* /usr/lib/libWPEBackend* /opt/wpe-sfos/lib/*.so* 2>/dev/null; echo ---; find / -xdev -name "libWPEBackend*" -o -xdev -name "*WPEBackend*" 2>/dev/null | head -20'

echo
echo "== runtime-common.sh: backend / renderer / env lines"
$SSH 'grep -n -i "backend\|renderer\|WPE_\|EGL\|hybris\|export " /opt/wpe-sfos/libexec/atlantic/runtime-common.sh 2>/dev/null | head -80'

echo
echo "== atlantic-browser NEEDED + dlopen strings"
$SSH 'readelf -d /usr/bin/atlantic-browser.bin 2>/dev/null | grep -E "NEEDED|RPATH|RUNPATH"; echo ---; strings /usr/bin/atlantic-browser.bin 2>/dev/null | grep -i "libWPEBackend\|wpe_loader\|WPE_BACKEND\|renderer-host\|libwpe" | sort -u | head -20'

echo
echo "== which backend name does libWPEWebKit default to / look for"
$SSH 'strings /usr/lib64/libWPEWebKit-2.0.so.1.11.4 2>/dev/null | grep -E "^libWPEBackend.*\.so|WPEBackend-default|libWPEBackend-fdo" | sort -u | head -20'

echo
echo "== libwpe loader symbols"
$SSH 'nm -D --defined-only /usr/lib64/libwpe-1.0.so.1.10.0 2>/dev/null | grep -i "loader\|view_backend" | head -40'

echo
echo "== wpe-sfos private symbols: where defined"
$SSH 'for L in /usr/lib64/libWPEWebKit-2.0.so.1.11.4 /usr/lib64/libwpe-1.0.so.1.10.0 /usr/lib64/libWPEBackend-fdo-1.0.so.1.11.0 /usr/lib64/wpe-compat/*.so*; do n=$(nm -D --defined-only "$L" 2>/dev/null | grep -c "wpe_sfos"); [ "$n" = 0 ] || echo "$L sfos_syms=$n"; done'
