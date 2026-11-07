#!/bin/sh
# VM-side: verify dev headers/tools for the WPE spike build.
set -u
echo "VM uname: $(uname -a)"
echo "--- gcc"
gcc --version | head -1
echo "--- headers"
for f in /usr/include/wayland-client-core.h /usr/include/wayland-client.h \
         /usr/include/wayland-util.h /usr/include/EGL/egl.h \
         /usr/include/glib-2.0/glib.h /usr/include/glib-2.0/glib-object.h \
         /usr/include/gio-unix-2.0/gio/gunixfdlist.h; do
  [ -f "$f" ] && echo "OK $f" || echo "MISSING $f"
done
echo "--- libs"
ls -l /usr/lib/aarch64-linux-gnu/libwayland-client.so /usr/lib/aarch64-linux-gnu/libglib-2.0.so 2>&1
echo "--- pkgconfig"
pkg-config --cflags --libs wayland-client glib-2.0 gio-2.0 gobject-2.0 2>&1
echo "--- sysroot dir"
mkdir -p /var/tmp/sd-webview-spike/include /var/tmp/sd-webview-spike/lib
ls -ld /var/tmp/sd-webview-spike
echo DONE
