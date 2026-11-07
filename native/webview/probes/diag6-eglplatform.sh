#!/bin/sh
# diag6: does `HYBRIS_EGLPLATFORM=wayland` let the WebProcess create its EGL
# window surface, and with a real Wayland connection does the fdo SHM export
# finally deliver frames?
#
# Background: without WAYLAND_DISPLAY the WebProcess starts and lives but no page
# is ever created (no load events). With lipstick's WAYLAND_DISPLAY it dies at
#   egl.c:418: eglCreateWindowSurface: Assertion `((struct ANativeWindow *) win)->common.magic
# which is libhybris refusing a plain wl_egl_window. This device ships
# /usr/lib64/libhybris/eglplatform_wayland.so (WaylandNativeWindow), selected by
# HYBRIS_EGLPLATFORM / EGL_PLATFORM, which wraps wl_egl_window into an
# ANativeWindow -- the thing the assertion wants.
#
# Takes the device lock itself (devlock.sh), runs a small env matrix, always
# kills WPE helpers and releases the lock.
set -u
BASE=/home/art/test/webview-diag6
OUT=$BASE/out
SPIKE=$BASE/wpe_offscreen_spike
WL=../../display/wayland-0      # lipstick's WAYLAND_DISPLAY (relative to XDG_RUNTIME_DIR)
XDG=/run/user/100000            # lipstick's XDG_RUNTIME_DIR
LOCK=/home/art/test/.device-lock
COMMON="WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1 JSC_numberOfFTLCompilerThreads=2 JSC_numberOfDFGCompilerThreads=2 JSC_numberOfBaselineCompilerThreads=2 JSC_numberOfGCMarkers=2 JSC_maxNumberOfWorklistThreads=4 WPE_BACKEND=libWPEBackend-fdo-1.0.so"

mkdir -p "$OUT"
echo "== diag6 start $(date -u +%Y-%m-%dT%H:%M:%SZ) wxh=720x1280"
echo "== wayland socket present: $(ls -l /run/display/wayland-0 2>/dev/null || echo MISSING /run/display/wayland-0)"
echo "== lipstick pid: $(pgrep -f lipstick | head -1)"

run_variant() {
    name="$1"; shift
    d="$OUT/$name"; mkdir -p "$d"
    echo
    echo "== VARIANT=$name"
    echo "   extra env: $*"
    ( sleep 13; pkill -9 -f wpe_offscreen_spike 2>/dev/null ) &
    WD=$!
    # shellcheck disable=SC2068
    env -i HOME=/home/art PATH=/usr/bin:/bin:/usr/sbin:/sbin \
        LD_LIBRARY_PATH=/usr/lib64/wpe-compat:/usr/lib64 \
        SD_SPIKE_OUT="$d" $COMMON $@ "$SPIKE" 720 1280 > "$d/spike.log" 2>&1
    rc=$?
    kill -9 "$WD" 2>/dev/null
    ( sleep 2; pgrep -a -f 'wpe-webkit-2.0' >> "$d/procs.log" 2>&1 ) &
    frames=$(grep -c 'spike_frame|' "$d/spike.log" 2>/dev/null || echo 0)
    loads=$(grep -c 'spike_load|' "$d/spike.log" 2>/dev/null || echo 0)
    shm=$(grep -o 'shm_frames=[0-9]*' "$d/spike.log" 2>/dev/null | head -1)
    echo "   rc=$rc load_events=$loads frames=$frames $shm"
    grep -E 'spike_result|spike_load\||spike_frame\||spike_cookie|spike_backend|Assertion|assertion|SIGABRT|egl\.c' "$d/spike.log" 2>/dev/null | head -12 | sed 's/^/   | /'
    echo "   -- dmesg tail:"; dmesg 2>/dev/null | tail -4 | sed 's/^/   | /'
    pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
    pkill -9 -f wpe_offscreen_spike 2>/dev/null
    sleep 1
}

# W1: Skia on the compositor thread disabled + CPU raster forced (Jolla's
# Skia tile path may be what drags the compositor into EGL buffer allocation).
run_variant W1_skia_off_cpu_on WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=wayland \
    WEBKIT_USE_SKIA_FOR_COMPOSITION=0 WEBKIT_SKIA_ENABLE_CPU_RENDERING=1
# W2: Skia composition off, CPU raster left at its default.
run_variant W2_skia_off WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=wayland \
    WEBKIT_USE_SKIA_FOR_COMPOSITION=0
# W3: CPU raster + bitmap texture pool disabled (no GPU texture pool at all).
run_variant W3_cpu_on_bitmap_pool_off WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=wayland \
    WEBKIT_SKIA_ENABLE_CPU_RENDERING=1 WEBKIT_BITMAP_TEXTURE_POOL_DISABLED=1
# W4: no compositor connection at all -- can the page be created without EGL?
run_variant W4_no_wl_cpu_on WEBKIT_SKIA_ENABLE_CPU_RENDERING=1 WEBKIT_USE_SKIA_FOR_COMPOSITION=0

echo
echo "== after: helpers (should be empty)"
pgrep -a -f 'wpe-webkit-2.0' 2>/dev/null || true
echo
echo "== SUMMARY"
for d in "$OUT"/*/; do
    [ -f "$d/spike.log" ] || continue
    printf '%-32s loads=%s frames=%s %s fatal=%s\n' "$(basename "$d")" \
        "$(grep -c 'spike_load|' "$d/spike.log" 2>/dev/null || echo 0)" \
        "$(grep -c 'spike_frame|' "$d/spike.log" 2>/dev/null || echo 0)" \
        "$(grep -o 'shm_frames=[0-9]*' "$d/spike.log" 2>/dev/null | head -1)" \
        "$(grep -c 'Fatal\|Assertion' "$d/spike.log" 2>/dev/null || echo 0)"
done
echo "== diag6 done"
