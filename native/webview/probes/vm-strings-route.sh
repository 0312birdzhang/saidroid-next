#!/bin/sh
# Local (VM) symbol/string inspection of the device's own WPE libraries.
SYS=/var/tmp/sd-webview-spike/lib
W=$SYS/libWPEWebKit-2.0.so.1.11.4
echo "== skia/cpu-rendering env names in libWPEWebKit"
strings -a "$W" | grep -iE "SKIA|CPU_RENDERING|software.rendering|acceleration.policy" | sort -u | head -20
echo "== renderer host / offscreen target references"
strings -a "$W" | grep -iE "renderer.host|renderer_host|offscreen.target|OffscreenTarget" | sort -u | head -25
echo "== exported renderer/offscreen symbols"
nm -D --defined-only "$W" | awk '{print $NF}' | grep -E "renderer_backend|renderer_host|offscreen" | sort -u
echo "== who defines wpe_renderer_backend_egl_* (device libs)"
for L in "$SYS"/libWPEBackend-fdo-1.0.so.1.11.0 "$SYS"/libwpe-1.0.so.1.10.0; do
  echo "-- $L"
  nm -D --defined-only "$L" | awk '{print $NF}' | grep -E "renderer|offscreen|shm|initialize" | sort -u | head -25
done
