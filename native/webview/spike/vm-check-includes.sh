#!/bin/sh
# VM: check WPE header transitive deps (libsoup-3.0, jsc) and compile a trivial include.
set -u
SYSROOT=/var/tmp/sd-webview-spike
echo "== include root"
ls "$SYSROOT/include/wpe-webkit-2.0"/
echo "== jsc headers?"
ls -d "$SYSROOT/include/wpe-webkit-2.0"/jsc "$SYSROOT/include"/jsc 2>&1
echo "== libsoup-3.0 headers on VM"
ls -d /usr/include/libsoup-3.0 2>&1
ls /usr/include/libsoup-3.0/libsoup/soup.h 2>&1
echo "== jsc dirs on VM"
ls -d /usr/include/webkitgtk-*/jsc 2>&1
echo "== soup pkgconfig"
pkg-config --modversion libsoup-3.0 2>&1
cat > /tmp/inc_test.c <<'EOF'
#include <wpe/webkit.h>
#include <wpe/fdo.h>
#include <wpe/unstable/fdo-shm.h>
#include <wayland-client-core.h>
int main(void){ return 0; }
EOF
gcc -c -o /tmp/inc_test.o /tmp/inc_test.c \
  -I"$SYSROOT/include/wpe-webkit-2.0" -I"$SYSROOT/include/wpe-1.0" -I"$SYSROOT/include/wpe-fdo-1.0" \
  -I/usr/include/libsoup-3.0 -DWPE_ENABLE_XKB=1 \
  $(pkg-config --cflags glib-2.0 gio-2.0 gobject-2.0) 2>&1 | head -30
echo "include-exit=$?"
echo DONE
