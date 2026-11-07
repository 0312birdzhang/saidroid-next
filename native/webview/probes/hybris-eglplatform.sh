#!/bin/sh
# Read-only: find how libhybris picks its EGL platform, and whether a Wayland
# platform adapter exists that would let hybris eglCreateWindowSurface accept a
# wl_egl_window (the assertion we hit is hybris's ANativeWindow magic check).
set -u
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"

echo "== libhybris eglplatform modules"
$SSH 'ls -l /usr/lib64/libhybris/ 2>/dev/null | head -30; echo ---; ls -l /usr/lib64/libhybris/*.so 2>/dev/null'

echo
echo "== env var names understood by libEGL / hybris"
$SSH 'for f in /usr/lib64/libEGL.so.1 /usr/lib64/libhybris-common.so.1 /usr/lib64/libhybris/eglplatform_wayland.so; do echo "-- $f"; strings -a "$f" 2>/dev/null | grep -E "HYBRIS|EGL_PLATFORM|eglplatform|ANDROID_NATIVE_WINDOW_MAGIC|wl_egl_window" | sort -u | head -20; done'

echo
echo "== who provides eglGetDisplay/eglCreateWindowSurface (hybris vs mesa)"
$SSH 'ls -l /usr/lib64/libEGL.so.1 /usr/lib64/libEGL.so 2>/dev/null; nm -D /usr/lib64/libEGL.so.1 2>/dev/null | grep -E "eglCreateWindowSurface|eglGetPlatformDisplay" | head; echo ---; strings -a /usr/lib64/libEGL.so.1 | grep -E "^libhybris|eglplatform_|_ZN7android" | sort -u | head -20'

echo
echo "== hybris wayland platform adapter: exported symbols"
$SSH 'nm -D --defined-only /usr/lib64/libhybris/eglplatform_wayland.so 2>/dev/null | head -30'

echo
echo "== libwayland-egl: upstream or hybris wrapper?"
$SSH 'ls -l /usr/lib64/libwayland-egl* ; nm -D --defined-only /usr/lib64/libwayland-egl.so.1 2>/dev/null | grep -E "wl_egl_window" | head'

echo
echo "== WebKit: which env vars does it read at startup (backend/egl related)"
$SSH 'strings -a /usr/lib64/libWPEWebKit-2.0.so.1.11.4 | grep -E "^(WEBKIT|WPE|LIBGL|EGL|HYBRIS)_[A-Z_0-9]+$" | sort -u | head -60'
