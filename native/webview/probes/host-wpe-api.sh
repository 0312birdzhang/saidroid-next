#!/bin/sh
# Inspect WPE WebKit GLib API surface + pkg-config + helper paths on device.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"

echo "===== pkgconfig files"
$SSH 'ls /usr/lib64/pkgconfig/ 2>/dev/null | grep -i -E "wpe|webkit"; echo ---; cat /usr/lib64/pkgconfig/wpe-webkit-2.0.pc /usr/lib64/pkgconfig/wpe-1.0.pc /usr/lib64/pkgconfig/wpebackend-fdo-1.0.pc 2>&1'

echo "===== WebKitWebView.h key decls"
$SSH 'grep -n -E "webkit_web_view_new|snapshot|run_javascript|evaluate_javascript|load_uri|load_html|get_estimated|set_zoom|session|context" /usr/include/wpe-webkit-2.0/wpe/WebKitWebView.h 2>&1 | head -80'

echo "===== headers list"
$SSH 'ls /usr/include/wpe-webkit-2.0/wpe/ 2>&1 | head -80'

echo "===== WebKitWebViewBackend.h"
$SSH 'sed -n 1,120p /usr/include/wpe-webkit-2.0/wpe/WebKitWebViewBackend.h 2>&1'

echo "===== wpe_fdo header"
$SSH 'ls /usr/include/wpe-fdo-1.0/wpe/ 2>&1; sed -n 1,200p /usr/include/wpe-fdo-1.0/wpe/fdo.h 2>&1 | head -120'

echo "===== libwpe header"
$SSH 'ls /usr/include/wpe-1.0/wpe/ 2>&1; grep -n -E "wpe_view_backend_create|struct wpe_view_backend_interface" /usr/include/wpe-1.0/wpe/view-backend.h 2>&1'

echo "===== helpers"
$SSH 'ls -la /usr/libexec/wpe-webkit-2.0/ /opt/wpe-sfos/libexec/wpe-webkit-2.0/ 2>&1'

echo "===== webkit env / injected bundle"
$SSH 'ls -la /opt/wpe-sfos/lib/wpe-webkit-2.0/injected-bundle/ 2>&1'

echo "===== soname deps of libWPEWebKit"
$SSH 'readelf -d /usr/lib64/libWPEWebKit-2.0.so.1.11.4 2>/dev/null | grep -E "NEEDED|SONAME" | head -40'

echo "===== glib version/headers"
$SSH 'ls /usr/include/glib-2.0/glib.h 2>&1; rpm -qa | grep -E "^glib2|^glibc" | head'

echo "===== device glibc"
$SSH 'ls -l /lib64/libc.so.6; /lib64/libc.so.6 2>&1 | head -1; rpm -q glibc 2>&1'

echo "===== atlantic desktop file"
$SSH 'cat /usr/share/applications/atlantic-browser.desktop 2>&1'

echo "DONE"
