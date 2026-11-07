#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH 'F=/usr/lib64/libWPEBackend-fdo-1.0.so.1.11.0
echo "=== exported wpe_ symbols ==="; nm -D --defined-only $F | grep -i wpe | head -40
echo "=== strings offscreen/renderer ==="; strings $F | grep -iE "offscreen|renderer_backend|exportable|shm" | head -20
echo "=== libwpe exported offscreen ==="; nm -D --defined-only /usr/lib64/libwpe-1.0.so.1 | grep -iE "offscreen|renderer" | head -20
echo "=== eglplatform_hwcomposer symbols ==="; nm -D --defined-only /usr/lib64/libhybris/eglplatform_hwcomposer.so | grep -iE "hybris_egl|native_window|platform" | head -20
echo "=== WPEWebProcess needs ==="; ldd /opt/wpe-sfos/libexec/wpe-webkit-2.0/WPEWebProcess 2>/dev/null | grep -iE "wpe|egl|gles|hybris" | head -20'
