#!/bin/sh
# Device-side diagnostic: why does the WPE UI process never spawn WPEWebProcess?
# Runs under the shared device lock, kills every WPE helper on exit.
#
# Installed by native/webview/probes/vm-diag-launch.sh; expects the spike binary
# at /home/art/test/webview-spike/wpe_offscreen_spike.
set -u
OUT=/home/art/test/webview-diag
LOCK=/home/art/test/.device-lock
SPIKE_DIR=/home/art/test/webview-spike
LOG="$OUT/diag.log"

mkdir -p "$OUT" || exit 1
: > "$LOG"
log() { echo "$*" >> "$LOG"; }

cleanup() {
    pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
    pkill -9 -f 'wpe_offscreen_spike' 2>/dev/null
    sleep 1
    rm -rf "$LOCK" 2>/dev/null
}
trap cleanup EXIT INT TERM

if mkdir "$LOCK" 2>/dev/null; then
    echo "diag1($(date +%s))" > "$LOCK/owner"
    log "LOCK_ACQUIRED"
else
    log "LOCK_BUSY $(cat "$LOCK/owner" 2>/dev/null)"
    exit 3
fi

# ---- 1. where is the compositor socket? -----------------------------------
log "== wayland sockets"
{ ls -l /run/display 2>/dev/null; find /run -maxdepth 3 -name 'wayland-*' 2>/dev/null; } >> "$LOG" 2>&1
log "== xdg runtime dirs"
ls -ld /run/user/* 2>/dev/null >> "$LOG" 2>&1
log "== lipstick env (wayland display of the running compositor)"
LIP=$(pgrep -f 'lipstick' | head -1)
if [ -n "${LIP:-}" ]; then
    tr '\0' '\n' < "/proc/$LIP/environ" 2>/dev/null | grep -E '^(WAYLAND_DISPLAY|XDG_RUNTIME_DIR|USER|HOME)=' >> "$LOG" 2>&1
fi

# ---- 2. strace the UI process: does it even try to exec the helper? -------
log "== strace run (9 s, execve/clone only)"
cd "$SPIKE_DIR" || exit 1
export HOME=/home/art
export XDG_RUNTIME_DIR=/tmp/sdspike-xdg
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LD_LIBRARY_PATH=/usr/lib64/wpe-compat:/usr/lib64
export LD_PRELOAD=/usr/lib64/wpe-compat/libsigill_skip.so
export WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1
export WEBKIT_SKIA_ENABLE_CPU_RENDERING=1
export WPE_BACKEND=libWPEBackend-fdo-1.0.so
( sleep 9; pkill -9 -f wpe_offscreen_spike ) &
strace -f -e trace=execve,clone3,wait4 -o "$OUT/strace.log" ./wpe_offscreen_spike 720 1280 >> "$OUT/spike-strace.log" 2>&1
log "EXIT=$?"
pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
log "== execve attempts seen (tail)"
grep -E 'execve\(' "$OUT/strace.log" 2>/dev/null | tail -20 >> "$LOG"
log "== WPEWebProcess mentions in strace"
grep -c 'WPEWebProcess' "$OUT/strace.log" 2>/dev/null >> "$LOG"
grep 'WPEWebProcess' "$OUT/strace.log" 2>/dev/null | head -10 >> "$LOG"
log "== strace size"
wc -l "$OUT/strace.log" 2>/dev/null >> "$LOG"
log "== spike log tail"
tail -12 "$OUT/spike-strace.log" >> "$LOG" 2>&1

# ---- 3. try again with the compositor's Wayland display in env ------------
log "== variant B: WAYLAND_DISPLAY from lipstick"
WD=""
if [ -n "${LIP:-}" ]; then
    WD=$(tr '\0' '\n' < "/proc/$LIP/environ" 2>/dev/null | sed -n 's/^WAYLAND_DISPLAY=//p')
fi
log "WAYLAND_DISPLAY_CANDIDATE=${WD:-none}"
if [ -n "$WD" ]; then
    export WAYLAND_DISPLAY="$WD"
    export XDG_RUNTIME_DIR=/run/user/100000
    ( sleep 9; pkill -9 -f wpe_offscreen_spike ) &
    ./wpe_offscreen_spike 720 1280 >> "$OUT/spike-variantB.log" 2>&1
    log "VARIANT_B_EXIT=$?"
    log "== variant B: helpers alive during run"
else
    log "VARIANT_B_SKIPPED no compositor env"
fi
pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
log "== done"
