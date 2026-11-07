#!/bin/sh
# diag5: does `HYBRIS_EGLPLATFORM=wayland` let the WebProcess create its EGL
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
BASE=/home/art/test/webview-diag5
OUT=$BASE/out
SPIKE=$BASE/wpe_offscreen_spike
WL=../../display/wayland-0      # lipstick's WAYLAND_DISPLAY (relative to XDG_RUNTIME_DIR)
XDG=/run/user/100000            # lipstick's XDG_RUNTIME_DIR
LOCK=/home/art/test/.device-lock
COMMON="WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1 JSC_numberOfFTLCompilerThreads=2 JSC_numberOfDFGCompilerThreads=2 JSC_numberOfBaselineCompilerThreads=2 JSC_numberOfGCMarkers=2 JSC_maxNumberOfWorklistThreads=4 WPE_BACKEND=libWPEBackend-fdo-1.0.so"

mkdir -p "$OUT"
echo "== diag5 start $(date -u +%Y-%m-%dT%H:%M:%SZ) wxh=720x1280"
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

# V1: the hypothesis -- hybris wayland platform, real compositor connection.
run_variant V1_hybris_wayland WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=wayland
# V2: same, plus Atlantic's preload set (sigill skip + egl stubs + sync skip).
run_variant V2_hybris_wayland_atlantic_preload WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=wayland \
    LD_PRELOAD=/usr/lib64/wpe-compat/libsigill_skip.so:/usr/lib64/wpe-compat/libegl-stubs.so:/usr/lib64/wpe-compat/libsyncskip.so \
    ATLANTIC_SKIP_SWAP_FENCE=1
# V3: EGL_PLATFORM is the other name libEGL honours.
run_variant V3_egl_platform_wayland WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG EGL_PLATFORM=wayland HYBRIS_EGLPLATFORM=wayland
# V4: V1 + the Skia/CPU-raster knobs this build actually honours (strings-checked).
run_variant V5_hybris_wayland_skia_cpu WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=wayland \
    WEBKIT_SKIA_ENABLE_CPU_RENDERING=1 WEBKIT_RASTER_ON_COMPOSITOR_THREAD=1 WEBKIT_TILE_GPU_READBACK_SYNC=1
# V6: control -- wayland connection but no platform override (expect the assert).
run_variant V4_control_no_platform WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG

echo
echo "== after: helpers (should be empty)"
pgrep -a -f 'wpe-webkit-2.0' 2>/dev/null || true
echo
echo "== SUMMARY"
for d in "$OUT"/*/; do
    [ -f "$d/spike.log" ] || continue
    name=$(basename "$d")
    printf '%-34s loads=%s frames=%s %s\n' "$name" \
        "$(grep -c 'spike_load|' "$d/spike.log" 2>/dev/null || echo 0)" \
        "$(grep -c 'spike_frame|' "$d/spike.log" 2>/dev/null || echo 0)" \
        "$(grep -o 'shm_frames=[0-9]*' "$d/spike.log" 2>/dev/null | head -1)"
done
echo "== diag5 done"
