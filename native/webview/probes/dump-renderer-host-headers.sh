#!/bin/sh
# Read-only: dump the WPE host-side headers that decide whether a windowless
# (offscreen / renderer-host) rendering path is available on this Sailfish build.
# Prints to stdout; caller redirects. No processes are started, no state changes.
set -u
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"

echo "== header inventory"
$SSH 'ls -1 /usr/include/wpe-1.0/wpe/ 2>/dev/null; echo ---; ls -1 /usr/lib/pkgconfig/*.pc 2>/dev/null | grep -i wpe'

echo
echo "== wpe/renderer-host.h"
$SSH 'cat /usr/include/wpe-1.0/wpe/renderer-host.h 2>/dev/null || echo NO_RENDERER_HOST_H'

echo
echo "== wpe/renderer-backend-egl.h"
$SSH 'cat /usr/include/wpe-1.0/wpe/renderer-backend-egl.h 2>/dev/null || echo NO_RENDERER_BACKEND_EGL_H'

echo
echo "== wpe/view-backend.h (renderer host hooks only)"
$SSH 'sed -n "1,200p" /usr/include/wpe-1.0/wpe/view-backend.h 2>/dev/null | grep -n -A3 -B3 -i "renderer_host\|interface {" || echo NO_VIEW_BACKEND_H'

echo
echo "== offscreen target API surface"
$SSH 'grep -rn "offscreen" /usr/include/wpe-1.0/ 2>/dev/null | head -40'

echo
echo "== libwpe exported renderer API"
$SSH 'nm -D --defined-only /usr/lib64/libwpe-1.0.so.1.10.0 2>/dev/null | grep -i "wpe_renderer\|offscreen\|renderer_host"'

echo
echo "== pkgconfig wpe-1.0"
$SSH 'cat /usr/lib64/pkgconfig/wpe-1.0.pc 2>/dev/null || cat /usr/lib/pkgconfig/wpe-1.0.pc 2>/dev/null'
