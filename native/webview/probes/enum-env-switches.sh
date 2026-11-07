#!/bin/sh
# Offline env-switch enumeration from the device libraries copied into the VM
# sysroot. Read-only, no device, no lock.
LIBS="/var/tmp/sd-webview-spike/lib/libWPEWebKit-2.0.so.1.11.4"
[ -e /var/tmp/sd-webview-spike/lib/libWPEBackend-fdo-1.0.so.1.11.0 ] && \
    LIBS="$LIBS /var/tmp/sd-webview-spike/lib/libWPEBackend-fdo-1.0.so.1.11.0"
[ -e /var/tmp/sd-webview-spike/lib/libwpe-1.0.so.1.10.0 ] && \
    LIBS="$LIBS /var/tmp/sd-webview-spike/lib/libwpe-1.0.so.1.10.0"
echo "LIBS=$LIBS"
for f in $LIBS; do echo "  $(ls -l "$f" | awk '{print $5}') $f"; done
echo "== step1: all ^WPE_ / ^LIBGL_ / ^HYBRIS_ strings =="
for f in $LIBS; do
    echo "## $(basename "$f")"
    strings -a "$f" | grep -E '^(WPE_|LIBGL_|HYBRIS_)' | sort -u
done
echo "== step1b: ^WEBKIT_ switches (same libs, for completeness) =="
for f in $LIBS; do
    echo "## $(basename "$f")"
    strings -a "$f" | grep -E '^WEBKIT_[A-Z0-9_]+$' | sort -u
done
echo "== step1c: any *_RENDER_MODE / *_BACKEND_* / FORCE_* switch-looking names =="
for f in $LIBS; do
    echo "## $(basename "$f")"
    strings -a "$f" | grep -E '^(WPE|WEBKIT|HYBRIS|LIBGL)_[A-Z0-9_]*(MODE|BACKEND|FORCE|OFFSCREEN|TARGET|EGL)[A-Z0-9_]*$' | sort -u
done
