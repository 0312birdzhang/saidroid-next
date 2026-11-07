#!/bin/sh
# Device-side diagnostic #2: is WPEWebProcess (a) never forked, (b) forked and
# died, or (c) up but never connected?  Answers with three independent kinds of
# evidence: execve/wait4 syscall trace, 0.2 s pgrep sampling, and dmesg/kernel log.
#
# Phases:  A strace + fine sampler   B WEBKIT_DEBUG + compositor WAYLAND_DISPLAY
# Takes and releases the shared device lock itself.  Hard-capped near 100 s.
set -u
OUT=/home/art/test/webview-diag2
LOCK=/home/art/test/.device-lock
SPIKE_DIR=/home/art/test/webview-spike
LOG="$OUT/diag2.log"

mkdir -p "$OUT" 2>/dev/null; : > "$LOG"
log() { echo "$*" >> "$LOG"; }

cleanup() {
    pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
    pkill -9 -f 'wpe_offscreen_spike' 2>/dev/null
    pkill -9 -f 'strace -f' 2>/dev/null
    sleep 1
    rm -rf "$LOCK" 2>/dev/null
}
trap cleanup EXIT INT TERM

# ---- 0. clean start ------------------------------------------------------
cleanup
if mkdir "$LOCK" 2>/dev/null; then
    echo "diag2-sd-webview($(date +%s))" > "$LOCK/owner"
    log "LOCK_ACQUIRED $(cat "$LOCK/owner")"
else
    log "LOCK_BUSY $(cat "$LOCK/owner" 2>/dev/null)"
    exit 3
fi
log "PGREP_CLEAN=$(pgrep -a -f 'wpe-webkit-2.0' | wc -l) ($(pgrep -a -f 'wpe-webkit-2.0' | tr '\n' ' '))"

cd "$SPIKE_DIR" || exit 1
export HOME=/home/art
export XDG_RUNTIME_DIR=/tmp/sdspike-xdg
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LD_LIBRARY_PATH=/usr/lib64/wpe-compat:/usr/lib64
export LD_PRELOAD=/usr/lib64/wpe-compat/libsigill_skip.so
export WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1
export WEBKIT_SKIA_ENABLE_CPU_RENDERING=1
export WPE_BACKEND=libWPEBackend-fdo-1.0.so

log "== ENV"
log "HOME=$HOME XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-<unset>}"
log "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
log "LD_PRELOAD=$LD_PRELOAD"
log "WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=${WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS:-<unset>} WEBKIT_FORCE_SANDBOX=${WEBKIT_FORCE_SANDBOX:-<unset>}"
log "WEBKIT_ENABLE_SECCOMP_FILTER=${WEBKIT_ENABLE_SECCOMP_FILTER:-<unset>} WPE_BACKEND=$WPE_BACKEND"
log "PATH=$PATH"
log "== ldd spike"
ldd ./wpe_offscreen_spike >> "$LOG" 2>&1

log "== what the UI process would print on a failed launch (strings)"
strings -a /usr/lib64/libWPEWebKit-2.0.so.1.11.4 | grep -iE "failed to launch|could not (launch|spawn)|Launching process|process did (crash|exit)|WebProcessProxy::(didFinishLaunching|processDidExit)" | sort -u | head -12 >> "$LOG" 2>&1

# ---- 1. compositor wayland display, for variant B ------------------------
LIP=$(pgrep -f 'lipstick' | head -1)
log "== lipstick pid=${LIP:-none}"
if [ -n "${LIP:-}" ]; then
    tr '\0' '\n' < "/proc/$LIP/environ" 2>/dev/null | grep -E '^(WAYLAND_DISPLAY|XDG_RUNTIME_DIR)=' >> "$LOG" 2>&1
fi
WD=""
[ -n "${LIP:-}" ] && WD=$(tr '\0' '\n' < "/proc/$LIP/environ" 2>/dev/null | sed -n 's/^WAYLAND_DISPLAY=//p')

# ---- 2. PHASE A: syscall trace + 0.2 s sampler ---------------------------
log ""
log "== PHASE A: strace execve/wait4 + 200ms pgrep sampling (10 s)"
: > "$OUT/pgrep-samples.txt"
: > "$OUT/dmesg-before.txt"
dmesg | tail -3 >> "$OUT/dmesg-before.txt" 2>&1
(
  i=0
  while [ "$i" -lt 100 ]; do
      printf 't=%5.1fs %s\n' "$(echo "$i" | awk '{printf "%.1f", $1/5}')" \
          "$(pgrep -f 'WPEWebProcess|WPENetworkProcess|WebKitWebProcess' | tr '\n' ' ')" \
          >> "$OUT/pgrep-samples.txt"
      sleep 0.2
      i=$((i+1))
  done
) &
SAMPLER=$!
( sleep 10; pkill -9 -f wpe_offscreen_spike ) &
strace -f -e trace=execve,execveat,clone,clone3,wait4,exit_group -o "$OUT/strace-A.log" \
       ./wpe_offscreen_spike 720 1280 > "$OUT/spike-A.log" 2>&1
RC=$?
log "PHASE_A_EXIT=$RC"
kill -9 "$SAMPLER" 2>/dev/null
log "== PHASE A: execve attempts (all)"
grep -E 'execve(at)?\(' "$OUT/strace-A.log" 2>/dev/null | sed 's/, ".*//' | sort | uniq -c | sort -rn | head -12 >> "$LOG"
log "== PHASE A: any WPEWebProcess in the trace? count="
grep -c 'WPEWebProcess' "$OUT/strace-A.log" 2>/dev/null >> "$LOG"
grep 'WPEWebProcess' "$OUT/strace-A.log" 2>/dev/null | head -6 >> "$LOG"
log "== PHASE A: nonzero wait4 statuses (child exits)"
grep 'WIFSIGNALED\|WEXITSTATUS' "$OUT/strace-A.log" 2>/dev/null | grep -v 'WEXITSTATUS(s) == 0' | head -8 >> "$LOG"
log "== PHASE A: pgrep samples (only lines where something was alive)"
grep -v 't=[ 0-9.]*s $' "$OUT/pgrep-samples.txt" | head -20 >> "$LOG"
log "== PHASE A: spike log"
grep -E 'SDWEBVIEW=' "$OUT/spike-A.log" | head -12 >> "$LOG"
log "== PHASE A: spike stderr non-SDWEBVIEW lines (first 15)"
grep -v 'SDWEBVIEW=' "$OUT/spike-A.log" | head -15 >> "$LOG"
log "== PHASE A: dmesg tail"
dmesg | tail -12 >> "$LOG" 2>&1
pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
sleep 1

# ---- 3. PHASE B: compositor WAYLAND_DISPLAY + WEBKIT_DEBUG ---------------
log ""
log "== PHASE B: WAYLAND_DISPLAY=${WD:-none} + WEBKIT_DEBUG=all (6 s)"
if [ -n "$WD" ]; then
    export WAYLAND_DISPLAY="$WD"
    export XDG_RUNTIME_DIR=/run/user/100000
    export WEBKIT_DEBUG=all
    ( sleep 6; pkill -9 -f wpe_offscreen_spike ) &
    ./wpe_offscreen_spike 720 1280 > "$OUT/spike-B.log" 2>&1
    log "PHASE_B_EXIT=$?"
    log "== PHASE B: helpers seen"
    pgrep -a -f 'wpe-webkit-2.0' >> "$LOG" 2>&1
    log "== PHASE B: debug lines about process launch / web process"
    grep -iE 'WebProcess|launch|sandbox|seccomp|ProcessLaunch' "$OUT/spike-B.log" | head -25 >> "$LOG"
    log "== PHASE B: SDWEBVIEW lines"
    grep -E 'SDWEBVIEW=' "$OUT/spike-B.log" | head -12 >> "$LOG"
else
    log "PHASE_B_SKIPPED no WAYLAND_DISPLAY from lipstick"
fi
pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
sleep 1
log "== FINAL: pgrep after cleanup = $(pgrep -a -f 'wpe-webkit-2.0' | wc -l)"
log "DONE"
