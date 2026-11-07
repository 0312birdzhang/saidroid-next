#!/bin/sh
# Verify every undefined webkit_/wpe_ symbol in the spike is exported by the
# device-provided libraries in the sysroot (the spike links with
# --allow-shlib-undefined, so link success proves nothing by itself).
set -u
SYSROOT=/var/tmp/sd-webview-spike
BIN="$SYSROOT/wpe_offscreen_spike"
LIBS="$SYSROOT/lib/libWPEWebKit-2.0.so.1.11.4 $SYSROOT/lib/libwpe-1.0.so.1.10.0 $SYSROOT/lib/libWPEBackend-fdo-1.0.so.1.11.0 /usr/lib/aarch64-linux-gnu/libwayland-server.so.0"
tmp=$(mktemp -d)
for l in $LIBS; do nm -D --defined-only "$l" | awk '{print $3}' ; done | sort -u > "$tmp/exported"
nm -D --undefined-only "$BIN" | awk '{print $2}' | grep -E '^(webkit_|wpe_|wl_shm)' | sort -u > "$tmp/undef"
echo "== undefined (webkit/wpe/wl_shm): $(wc -l < "$tmp/undef")"
missing=$(comm -23 "$tmp/undef" "$tmp/exported")
if [ -n "$missing" ]; then echo "MISSING:"; echo "$missing"; else echo "ALL_RESOLVE"; fi
echo "== exported wpe_fdo/fdo symbols of interest"
grep -E 'wpe_fdo_initialize_shm|wpe_view_backend_exportable_fdo_(create|get_view_backend|dispatch_release_shm_exported_buffer|dispatch_frame_complete)|wpe_fdo_shm_exported_buffer_get_shm_buffer' "$tmp/exported" || echo "(none)"
echo "== symbol versions of key API (from libWPEWebKit)"
objdump -T "$SYSROOT/lib/libWPEWebKit-2.0.so.1.11.4" 2>/dev/null | grep -E 'webkit_web_view_get_snapshot|webkit_web_view_load_html|webkit_cookie_manager_get_cookies' | head
rm -rf "$tmp"
