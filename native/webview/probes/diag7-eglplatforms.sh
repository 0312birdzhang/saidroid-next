#!/bin/sh
# diag7: the three libhybris eglplatform backends we never tried.
#
# History: with no Wayland connection the WebProcess hangs before creating a page.
# With lipstick's Wayland connection and the default platform it aborts at
#   egl.c:418 eglCreateWindowSurface: Assertion ANativeWindow_MAGIC failed
# With HYBRIS_EGLPLATFORM=wayland it gets past that and then dies at
#   Fatal: the server doesn't advertise the android_wlegl global!
# Both failures come from libhybris trying to wrap a plain wl_egl_window.
# This device ships four eglplatform backends; hwcomposer and fbdev do not need
# Wayland buffers at all, so they are genuinely untested paths:
#   /usr/lib64/libhybris/eglplatform_hwcomposer.so
#   /usr/lib64/libhybris/eglplatform_fbdev.so
#   /usr/lib64/libhybris/eglplatform_null.so
#
# Each variant: 13 s, fresh out dir, spike is the same binary that already writes
# frames + a PNG. Judgement is machine-made by check-evidence.py on the host.
set -u
BASE=/home/art/test/webview-diag7
OUT=$BASE/out
SPIKE=$BASE/wpe_offscreen_spike
WL=../../display/wayland-0
XDG=/run/user/100000
COMMON="WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1 JSC_numberOfFTLCompilerThreads=2 JSC_numberOfDFGCompilerThreads=2 JSC_numberOfBaselineCompilerThreads=2 JSC_maxNumberOfWorklistThreads=4 WPE_BACKEND=libWPEBackend-fdo-1.0.so"

mkdir -p "$OUT"
echo "== diag7 start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "== eglplatform backends on device:"
ls -l /usr/lib64/libhybris/eglplatform_*.so 2>/dev/null | sed 's/^/   /'

# Offline env enumeration for the libs that only exist on the device (the big ones
# we already enumerated in the VM from copies). Anchored names only, no summary.
echo "== ENV_SWITCHES (device-side libs) =="
for f in /usr/lib64/libhybris/eglplatform_*.so /usr/lib64/libhybris/libhybris-common.so.1; do
    [ -e "$f" ] || continue
    echo "## $f"
    strings -a "$f" 2>/dev/null | grep -E '^(WPE_|LIBGL_|HYBRIS_|WEBKIT_)' | sort -u | sed 's/^/   /'
done
echo "== ENV_SWITCHES_END ==" 

run_variant() {
    name="$1"; shift
    d="$OUT/$name"; mkdir -p "$d"
    echo
    echo "== VARIANT=$name"
    echo "   env: $*"
    ( sleep 13; pkill -9 -f wpe_offscreen_spike 2>/dev/null ) &
    WD=$!
    # shellcheck disable=SC2068
    env -i HOME=/home/art PATH=/usr/bin:/bin:/usr/sbin:/sbin \
        LD_LIBRARY_PATH=/usr/lib64/wpe-compat:/usr/lib64 \
        SD_SPIKE_OUT="$d" $COMMON $@ "$SPIKE" 720 1280 > "$d/spike.log" 2>&1
    rc=$?
    kill -9 "$WD" 2>/dev/null
    loads=$(grep -c 'spike_load|' "$d/spike.log" 2>/dev/null || echo 0)
    frames=$(grep -c 'spike_frame|' "$d/spike.log" 2>/dev/null || echo 0)
    shm=$(grep -o 'shm_frames=[0-9]*' "$d/spike.log" 2>/dev/null | head -1)
    echo "   FRAMES=$frames LOAD_EVENTS=$loads $shm rc=$rc"
    grep -E 'spike_result|spike_backend|Assertion|assertion|Fatal|SIGABRT|egl\.c|error|Error' \
        "$d/spike.log" 2>/dev/null | head -10 | sed 's/^/   | /'
    echo "   -- dmesg tail:"; dmesg 2>/dev/null | tail -3 | sed 's/^/   | /'
    pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
    pkill -9 -f wpe_offscreen_spike 2>/dev/null
    sleep 1
}

# The three untested platforms. Wayland connection is kept because the WebProcess
# always builds a wl_surface for the view; the platform decides what the EGL
# window surface is made of.
run_variant P1_hwcomposer WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=hwcomposer
run_variant P2_fbdev      WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=fbdev
run_variant P3_null       WAYLAND_DISPLAY=$WL XDG_RUNTIME_DIR=$XDG HYBRIS_EGLPLATFORM=null

echo
echo "== diag7 done $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "== summary"
for d in "$OUT"/*; do
    [ -d "$d" ] || continue
    echo "   $(basename "$d"): FRAMES=$(grep -c 'spike_frame|' "$d/spike.log" 2>/dev/null || echo 0) \
LOADS=$(grep -c 'spike_load|' "$d/spike.log" 2>/dev/null || echo 0) \
$(grep -o 'shm_frames=[0-9]*' "$d/spike.log" 2>/dev/null | head -1)"
done
