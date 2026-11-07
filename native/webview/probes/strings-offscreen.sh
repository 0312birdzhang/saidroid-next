#!/bin/sh
# What does libWPEWebKit itself say about "offscreen"? If a mode switch exists it
# will show up as an env name or a log line; if only code paths exist, all we see
# are symbols.
LIB=/var/tmp/sd-webview-spike/lib/libWPEWebKit-2.0.so.1.11.4
echo "== strings -i offscreen (knob-looking lines only) =="
strings -a "$LIB" | grep -i 'offscreen' | sort -u | head -40
echo "== count of offscreen mentions =="
strings -a "$LIB" | grep -ic offscreen
echo "== offscreen-related dynamic symbols =="
nm -D "$LIB" 2>/dev/null | grep -i 'offscreen' | head -20
echo "== who calls wpe_renderer_backend_egl_offscreen_target_* ? (undefined refs) =="
nm -D --undefined-only "$LIB" 2>/dev/null | grep -i 'offscreen' | head -20
