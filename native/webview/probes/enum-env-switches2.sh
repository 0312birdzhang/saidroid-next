#!/bin/sh
# 1c) switch-looking names; 2) are the _wpe_* interface names defined or undefined?
LIB=/var/tmp/sd-webview-spike/lib
FDO=$LIB/libWPEBackend-fdo-1.0.so.1.11.0
WPELIB=$LIB/libwpe-1.0.so.1.10.0
WK=$LIB/libWPEWebKit-2.0.so.1.11.4
echo "== step1c switch-looking env names =="
for f in $WK $FDO $WPELIB; do
    echo "## $(basename "$f")"
    strings -a "$f" | grep -E '^(WPE|WEBKIT|HYBRIS|LIBGL)_[A-Z0-9_]*(MODE|BACKEND|FORCE|OFFSCREEN|TARGET|EGL)[A-Z0-9_]*$' | sort -u
done
echo "== step2: the three _wpe_* loader contract names in libWPEBackend-fdo =="
for n in _wpe_loader_interface _wpe_view_backend_interface _wpe_renderer_backend_egl_interface _wpe_renderer_backend_egl_target_interface _wpe_renderer_backend_egl_offscreen_target_interface _wpe_renderer_host_interface; do
    line=$(nm -D --defined-only "$FDO" 2>/dev/null | grep -w "$n")
    und=$(nm -D --undefined-only "$FDO" 2>/dev/null | grep -w "$n")
    if [ -n "$line" ]; then echo "DEFINED  $n :: $line"
    elif [ -n "$und" ]; then echo "UNDEF    $n :: $und"
    else echo "ABSENT   $n (neither defined nor undefined)"; fi
done
echo "== step2b: same names in libwpe (the loader) =="
for n in _wpe_loader_interface _wpe_view_backend_interface _wpe_renderer_backend_egl_offscreen_target_interface; do
    line=$(nm -D --defined-only "$WPELIB" 2>/dev/null | grep -w "$n")
    [ -n "$line" ] && echo "DEFINED  $n :: $line" || echo "ABSENT   $n in libwpe"
done
echo "== step2c: how does libwpe look the names up? (strings around loader) =="
strings -a "$WPELIB" | grep -nE '^_wpe_|libWPEBackend|wpe_loader' | head -20
echo "== step2d: does fdo contain the offscreen symbol as *data* (objdump -T) =="
objdump -T "$FDO" 2>/dev/null | grep -E '_wpe_renderer_backend_egl' || echo "(no such export in objdump -T)"
