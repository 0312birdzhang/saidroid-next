#!/bin/sh
# Device-side experiment: the SFOS WebProcess reaches hybris EGL and aborts with
# "eglCreateWindowSurface: Assertion (... ANDROID_NATIVE_WINDOW_MAGIC)".
# Atlantic preloads three compat shims; try the same set and see whether the
# WebProcess gets past that assertion and exports frames.  VM wrapper holds lock.
set -u
OUT=/home/art/test/webview-diag4
SPIKE_DIR=/home/art/test/webview-spike
LOG="$OUT/diag4.log"
mkdir -p "$OUT/out" 2>/dev/null; : > "$LOG"
log() { echo "$*" >> "$LOG"; }
killall_wpe() { pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null; pkill -9 -f 'wpe_offscreen_spike' 2>/dev/null; }
trap 'killall_wpe; sleep 1' EXIT INT TERM
killall_wpe; sleep 1
cd "$SPIKE_DIR" || exit 1

LIP=$(pgrep -f 'lipstick' | head -1)
WD=$(tr '\0' '\n' < "/proc/$LIP/environ" 2>/dev/null | sed -n 's/^WAYLAND_DISPLAY=//p')
log "lipstick=$LIP WAYLAND_DISPLAY=$WD"

export HOME=/home/art
export XDG_RUNTIME_DIR=/run/user/100000
export WAYLAND_DISPLAY="$WD"
export LD_LIBRARY_PATH=/usr/lib64/wpe-compat:/usr/lib64:/opt/wpe-sfos/lib
export ATLANTIC_SKIP_SWAP_FENCE=1
export WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1
export WPE_BACKEND=libWPEBackend-fdo-1.0.so

run_variant() {
    name=$1; preload=$2; shift 2
    log ""
    log "== VARIANT $name  LD_PRELOAD=$preload"
    if [ -n "$preload" ]; then export LD_PRELOAD="$preload"; else unset LD_PRELOAD; fi
    rm -rf "$OUT/out"; mkdir -p "$OUT/out"
    ( sleep 10; pkill -9 -f wpe_offscreen_spike ) &
    SD_SPIKE_OUT="$OUT/out" ./wpe_offscreen_spike 720 1280 > "$OUT/$name.log" 2>&1
    log "EXIT=$?"
    log "-- WPE stderr (non-SDWEBVIEW):"
    grep -v 'SDWEBVIEW=' "$OUT/$name.log" | head -8 >> "$LOG" 2>&1
    log "-- frames: $(ls "$OUT/out" 2>/dev/null | tr '\n' ' ')"
    log "-- key: $(grep -E 'spike_result|spike_load\|' "$OUT/$name.log" | head -4 | tr '\n' ' ')"
    killall_wpe; sleep 1
}

run_variant A_none ""
run_variant B_sigill "/usr/lib64/wpe-compat/libsigill_skip.so"
run_variant C_atlantic_set "/usr/lib64/wpe-compat/libsigill_skip.so:/usr/lib64/wpe-compat/libegl-stubs.so:/usr/lib64/wpe-compat/libsyncskip.so"
log ""
log "== dmesg tail"
dmesg | tail -6 >> "$LOG" 2>&1
log "DONE"
