#!/bin/sh
# Read-only: determine the exact backend ABI contract (struct globals libwpe dlsyms)
# and whether WPEBackend-fdo implements the offscreen-target / renderer-host pieces.
set -u
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
FDO=/usr/lib64/libWPEBackend-fdo-1.0.so.1.11.0
LWPE=/usr/lib64/libwpe-1.0.so.1.10.0
WK=/usr/lib64/libWPEWebKit-2.0.so.1.11.4

echo "== libwpe loader: dlsym names + init order"
$SSH "strings -a $LWPE | grep -E '_interface$|^libWPEBackend|_backend_interface' | sort -u"
echo
echo "== fdo exported data/interface symbols"
$SSH "nm -D --defined-only $FDO | grep -E ' [BD] ' | head -40"
echo
echo "== fdo: any offscreen/hybrid/renderer-host symbol"
$SSH "nm -D $FDO | grep -i -E 'offscreen|renderer|hybris|android|native_window|shm' | head -40"
echo
echo "== libwpe offscreen_target_create disassembly (what it delegates to)"
$SSH "objdump -d --start-address=0x197e0 --stop-address=0x19860 $LWPE 2>/dev/null | sed -n '1,40p'"
echo
echo "== libwpe loader_init disassembly (symbol names it dlsyms)"
$SSH "objdump -d --start-address=0x19f20 --stop-address=0x1a090 $LWPE 2>/dev/null | grep -E 'adrp|add|bl|ldr' | head -60"
echo
echo "== strings in libwpe around loader symbol names"
$SSH "strings -a $LWPE | grep -E '^(view_backend|renderer_|interface|_interface)$|wpe_view_backend_create|wpe_renderer_backend_egl_' | sort -u | head -40"
echo
echo "== does WebKit look for an env to force backend / offscreen?"
$SSH "strings -a $WK | grep -E 'WPE_[A-Z_]*BACKEND|WPEBackend|offscreen|Offscreen' | sort -u | head -40"
echo
echo "== atlantic running? which backend libs mapped"
$SSH 'for p in $(pgrep -f atlantic 2>/dev/null); do echo "PID $p $(cat /proc/$p/comm)"; tr "\0" "\n" < /proc/$p/environ | grep -E "^(WAYLAND_DISPLAY|XDG_RUNTIME_DIR|WPE_|WEBKIT_|LD_LIBRARY_PATH|LD_PRELOAD)=" ; grep -o "/[^ ]*WPEBackend[^ ]*" /proc/$p/maps | sort -u; done; echo ATLANTIC_PIDS=$(pgrep -cf atlantic 2>/dev/null || echo 0)'
