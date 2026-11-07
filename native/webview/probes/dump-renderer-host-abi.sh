#!/bin/sh
echo "== /usr/include/wpe-1.0/wpe/renderer-host.h =="
sed -n '1,60p' /usr/include/wpe-1.0/wpe/renderer-host.h 2>/dev/null || echo NO_HEADER
echo "== /usr/include/wpe-1.0/wpe/renderer-backend-egl.h (iface structs) =="
sed -n '1,120p' /usr/include/wpe-1.0/wpe/renderer-backend-egl.h 2>/dev/null | grep -n -A12 'struct wpe_renderer_backend_egl' | head -60
