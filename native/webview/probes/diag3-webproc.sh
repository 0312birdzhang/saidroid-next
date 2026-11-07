#!/bin/sh
# Device-side diagnostic #3 (fixed: the spike needs SD_SPIKE_OUT or it exits with
# SDWEBVIEW=spike_error|no_out_dir, which voided diagnostic #2's phase A/B).
#
# Answers: is WPEWebProcess never forked, forked-and-died, or up-but-unconnected?
# Evidence: execve/wait4 strace (-s 300), 0.2 s pgrep sampling, helper ldd,
# manual helper run, and a variant that hands the WebProcess the compositor's
# real Wayland display.  The lock is held by the VM-side wrapper.
set -u
OUT=/home/art/test/webview-diag3
SPIKE_DIR=/home/art/test/webview-spike
LOG="$OUT/diag3.log"

mkdir -p "$OUT/outA" "$OUT/outB" 2>/dev/null; : > "$LOG"
log() { echo "$*" >> "$LOG"; }
killall_wpe() { pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null; pkill -9 -f 'wpe_offscreen_spike' 2>/dev/null; }
trap 'killall_wpe; sleep 1' EXIT INT TERM
killall_wpe
sleep 1

cd "$SPIKE_DIR" || exit 1
export HOME=/home/art
export XDG_RUNTIME_DIR=/tmp/sdspike-xdg
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LD_LIBRARY_PATH=/usr/lib64/wpe-compat:/usr/lib64
export LD_PRELOAD=/usr/lib64/wpe-compat/libsigill_skip.so
export WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1
export WEBKIT_SKIA_ENABLE_CPU_RENDERING=1
export WPE_BACKEND=libWPEBackend-fdo-1.0.so

log "== ENV (spike process)"
log "HOME=$HOME XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-<unset>} WAYLAND_SOCKET=${WAYLAND_SOCKET:-<unset>}"
log "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
log "LD_PRELOAD=$LD_PRELOAD"
log "WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=${WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS:-<unset>} WEBKIT_FORCE_SANDBOX=${WEBKIT_FORCE_SANDBOX:-<unset>} WEBKIT_ENABLE_SECCOMP_FILTER=${WEBKIT_ENABLE_SECCOMP_FILTER:-<unset>}"

log ""
log "== helper ldd (Lead item 2)"
ldd /usr/libexec/wpe-webkit-2.0/WPEWebProcess >> "$LOG" 2>&1
log "-- missing libs:"
ldd /usr/libexec/wpe-webkit-2.0/WPEWebProcess 2>&1 | grep -i 'not found' >> "$LOG" 2>&1 || log "NONE_MISSING"
log "-- bwrap present? $(ls -l /usr/bin/bwrap 2>&1)"

log ""
log "== manual helper run (Lead item 5): 3 s, capture its own complaint"
( sleep 3; pkill -9 -f 'WPEWebProcess' ) &
/usr/libexec/wpe-webkit-2.0/WPEWebProcess > "$OUT/helper-direct.log" 2>&1
log "HELPER_EXIT=$?"
head -20 "$OUT/helper-direct.log" >> "$LOG" 2>&1

# ---------------------------------------------------------------- PHASE A
log ""
log "== PHASE A: strace -f execve/clone3/wait4 -s 300, 10 s, SD_SPIKE_OUT set"
: > "$OUT/pgrep-samples.txt"
(
  i=0
  while [ "$i" -lt 55 ]; do
      printf 't=%4.1fs %s\n' "$i" "$(pgrep -f 'WPEWebProcess|WPENetworkProcess' | tr '\n' ' ')" >> "$OUT/pgrep-samples.txt"
      sleep 0.2
      i=$((i+1))
  done
) &
SAMPLER=$!
( sleep 11; pkill -9 -f wpe_offscreen_spike ) &
SD_SPIKE_OUT="$OUT/outA" strace -f -s 300 -e trace=execve,execveat,clone,clone3,wait4 \
    -o "$OUT/strace-A.log" ./wpe_offscreen_spike 720 1280 > "$OUT/spike-A.log" 2>&1
log "PHASE_A_EXIT=$?"
kill -9 "$SAMPLER" 2>/dev/null
log "-- helper execve attempts seen:"
grep -E 'execve(at)?\(' "$OUT/strace-A.log" 2>/dev/null | grep -E 'wpe-webkit|bwrap' | head -8 >> "$LOG"
log "-- execve of WPEWebProcess count: $(grep -c 'WPEWebProcess' "$OUT/strace-A.log" 2>/dev/null)"
log "-- execve of bwrap count: $(grep -c 'bwrap' "$OUT/strace-A.log" 2>/dev/null)"
log "-- all distinct execve paths:"
grep -oE 'execve(at)?\("[^"]+"' "$OUT/strace-A.log" 2>/dev/null | sed 's/.*("//' | sort | uniq -c >> "$LOG"
log "-- nonzero child exits:"
grep -E 'WIFSIGNALED|WEXITSTATUS' "$OUT/strace-A.log" 2>/dev/null | grep -v 'WEXITSTATUS(s) == 0' | head -6 >> "$LOG"
log "-- pgrep samples with something alive:"
awk '$2 != ""' "$OUT/pgrep-samples.txt" 2>/dev/null | head -12 >> "$LOG"
log "-- spike A key lines:"
grep -E 'SDWEBVIEW=' "$OUT/spike-A.log" | head -14 >> "$LOG"
log "-- frames in outA: $(ls "$OUT/outA" 2>/dev/null | tr '\n' ' ')"
killall_wpe; sleep 1

# ---------------------------------------------------------------- PHASE B
LIP=$(pgrep -f 'lipstick' | head -1)
WD=$(tr '\0' '\n' < "/proc/$LIP/environ" 2>/dev/null | sed -n 's/^WAYLAND_DISPLAY=//p')
WS=$(tr '\0' '\n' < "/proc/$LIP/environ" 2>/dev/null | sed -n 's/^WAYLAND_SOCKET=//p')
log ""
log "== PHASE B: lipstick pid=$LIP WAYLAND_DISPLAY=$WD WAYLAND_SOCKET=${WS:-<unset>} (8 s)"
export WAYLAND_DISPLAY="$WD"
export XDG_RUNTIME_DIR=/run/user/100000
( sleep 8; pkill -9 -f wpe_offscreen_spike ) &
SD_SPIKE_OUT="$OUT/outB" ./wpe_offscreen_spike 720 1280 > "$OUT/spike-B.log" 2>&1
log "PHASE_B_EXIT=$?"
log "-- helpers alive after B: $(pgrep -a -f 'wpe-webkit-2.0' | head -3 | tr '\n' ' ')"
log "-- spike B key lines:"
grep -E 'SDWEBVIEW=' "$OUT/spike-B.log" | head -14 >> "$LOG"
log "-- frames in outB: $(ls "$OUT/outB" 2>/dev/null | tr '\n' ' ')"
killall_wpe
log ""
log "== dmesg tail"
dmesg | tail -8 >> "$LOG" 2>&1
log "== FINAL pgrep wpe = $(pgrep -f 'wpe-webkit-2.0' | wc -l)"
log "DONE"
