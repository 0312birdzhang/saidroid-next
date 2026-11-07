#!/bin/sh
# Run the WPE offscreen spike on the Sailfish device and pull its evidence back.
#
# Usage (from the build VM, where the shared repo is /media/psf/Home/WorkSpace/saidroid-next):
#     /bin/sh native/webview/spike/vm-run-spike.sh [width height]
#     SD_SPIKE_DRYRUN=1 /bin/sh native/webview/spike/vm-run-spike.sh   # env preflight only
#
# Everything it touches on the device lives under /home/art/test/webview-spike/.
# It takes the shared device lock first, refuses to run when another ART instance
# holds it, and always kills the WPE helper processes before releasing the lock
# (a stray WPEWebProcess keeps the topmost compositor busy and makes later
# screenshots white).
set -u

W=${1:-720}
H=${2:-1280}
DRYRUN=${SD_SPIKE_DRYRUN:-0}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8"
SSH="sshpass -e ssh $SSH_OPTS root@192.168.2.15"
SCP="sshpass -e scp $SSH_OPTS"
REMOTE=/home/art/test/webview-spike
REPO=/media/psf/Home/WorkSpace/saidroid-next
DEST="$REPO/build/codex-api29/webview-spike"
BIN="${SD_SPIKE_BIN:-/var/tmp/sd-webview-spike/wpe_offscreen_spike}"
LOCK=/home/art/test/.device-lock

say() { echo "== $*"; }

say "device reachability"
$SSH "true" || { echo "DEVICE_UNREACHABLE"; exit 1; }

say "device lock"
if $SSH "mkdir '$LOCK' 2>/dev/null"; then
    HOLDER="vm-run-spike($(date +%s))"
    $SSH "echo '$HOLDER' > '$LOCK/owner'"
    ACQUIRED=1
    echo "LOCK_ACQUIRED $HOLDER"
else
    echo "LOCK_BUSY by: $($SSH "cat '$LOCK/owner' 2>/dev/null")"
    exit 3
fi

cleanup() {
    if [ "${ACQUIRED:-0}" = "1" ]; then
        # Kill every WPE helper we may have started, then release the lock.
        $SSH "pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null; pkill -9 -f 'WPEWebProcess' 2>/dev/null; pkill -9 -f 'wpe_offscreen_spike' 2>/dev/null; sleep 1" >/dev/null 2>&1
        $SSH "rm -rf '$LOCK'" >/dev/null 2>&1
        echo "LOCK_RELEASED"
    fi
}
trap cleanup EXIT INT TERM

say "stage binary (local: $BIN)"
[ -f "$BIN" ] || { echo "MISSING_BINARY $BIN"; exit 2; }
$SSH "rm -rf '$REMOTE' && mkdir -p '$REMOTE/out'"
$SCP "$BIN" "root@192.168.2.15:$REMOTE/wpe_offscreen_spike" || { echo "SCP_FAILED"; exit 4; }

say "write remote runner"
$SSH "cat > '$REMOTE/run.sh'" <<'EOS'
#!/bin/sh
# Environment mirrors the pieces of /opt/wpe-sfos/libexec/atlantic/runtime-common.sh
# that matter for a windowless SHM-rendered view.
set -u
OUT="$SD_SPIKE_OUT"
LOG="$OUT/spike.log"
PROC="$OUT/procs.log"
: > "$LOG"
: > "$PROC"
export HOME=/home/art
export XDG_RUNTIME_DIR=/tmp/sdspike-xdg
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LD_LIBRARY_PATH=/usr/lib64/wpe-compat:/usr/lib64
export LD_PRELOAD=/usr/lib64/wpe-compat/libsigill_skip.so
export WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=1
unset WEBKIT_FORCE_SANDBOX 2>/dev/null || true
export WEBKIT_SKIA_ENABLE_CPU_RENDERING=1
export WEBKIT_SKIA_CPU_PAINTING_THREADS=2
export JSC_numberOfFTLCompilerThreads=2
export JSC_numberOfDFGCompilerThreads=2
export JSC_numberOfBaselineCompilerThreads=2
export JSC_numberOfGCMarkers=2
export JSC_maxNumberOfWorklistThreads=4
export WEBKIT_DISABLE_SANDBOX=1
export WPE_BACKEND=libWPEBackend-fdo-1.0.so
cd "$(dirname "$0")" || exit 1

# ---- preflight: every env/path that, if wrong, yields "process starts, white
# ---- frame, no error message".  Printed so a run can be audited afterwards.
echo "PREFLIGHT=uname=$(uname -m) uid=$(id -u) cwd=$(pwd)" >> "$LOG"
echo "PREFLIGHT=HOME=$HOME XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR writable=$([ -w "$XDG_RUNTIME_DIR" ] && echo yes || echo no)" >> "$LOG"
echo "PREFLIGHT=LD_LIBRARY_PATH=$LD_LIBRARY_PATH" >> "$LOG"
echo "PREFLIGHT=LD_PRELOAD=$LD_PRELOAD" >> "$LOG"
echo "PREFLIGHT=WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS=$WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS" >> "$LOG"
echo "PREFLIGHT=WEBKIT_SKIA_ENABLE_CPU_RENDERING=$WEBKIT_SKIA_ENABLE_CPU_RENDERING" >> "$LOG"
echo "PREFLIGHT=WPE_BACKEND=$WPE_BACKEND" >> "$LOG"
for p in /usr/lib64/libWPEWebKit-2.0.so.1.11.4 \
         /usr/lib64/libWPEBackend-fdo-1.0.so.1.11.0 \
         /usr/lib64/libwpe-1.0.so.1.10.0 \
         /opt/wpe-sfos/libexec/wpe-webkit-2.0/WPEWebProcess \
         /opt/wpe-sfos/libexec/wpe-webkit-2.0/WPENetworkProcess \
         /opt/wpe-sfos/lib/wpe-webkit-2.0/injected-bundle/libWPEInjectedBundle.so \
         /usr/share/wpe-webkit-2.0 \
         /usr/lib64/wpe-compat/libsigill_skip.so; do
    if [ -e "$p" ]; then echo "PREFLIGHT=path_ok $p" >> "$LOG"; else echo "PREFLIGHT=path_MISSING $p" >> "$LOG"; fi
done
echo "PREFLIGHT=ldd_begin" >> "$LOG"
ldd ./wpe_offscreen_spike >> "$LOG" 2>&1
echo "PREFLIGHT=ldd_end" >> "$LOG"
if grep -q 'not found' "$LOG"; then echo "PREFLIGHT=RESULT=ldd_missing_libs" >> "$LOG"; else echo "PREFLIGHT=RESULT=ldd_ok" >> "$LOG"; fi

if [ "${SD_SPIKE_DRYRUN:-0}" = "1" ]; then
    echo "DRYRUN=done" >> "$LOG"
    exit 0
fi

# ---- process monitor: proves whether WPEWebProcess/WPENetworkProcess existed.
mon() {
    i=0
    while [ "$i" -lt 36 ]; do
        echo "== t=${i}s" >> "$PROC"
        pgrep -a -f 'wpe-webkit-2.0' >> "$PROC" 2>&1
        sleep 2
        i=$((i+2))
    done
}
mon &
MPID=$!

echo "WRAPPER=start ts=$(date +%s) size=$1x$2" >> "$LOG"
# ---- 25 s hard watchdog: the spike's own 20 s watchdog normally ends it first.
( sleep 25; pkill -9 -f wpe_offscreen_spike 2>/dev/null ) &
WPID=$!
./wpe_offscreen_spike "$1" "$2" >> "$LOG" 2>&1
RC=$?
kill -9 "$WPID" 2>/dev/null
kill -9 "$MPID" 2>/dev/null
echo "EXIT_CODE=$RC" >> "$LOG"
echo "AFTERMATH=remaining_wpe_processes:" >> "$LOG"
pgrep -a -f 'wpe-webkit-2.0' >> "$LOG" 2>&1
pkill -9 -f 'wpe-webkit-2.0' 2>/dev/null
echo "AFTERMATH=done" >> "$LOG"
EOS
$SSH "chmod 755 '$REMOTE/run.sh' '$REMOTE/wpe_offscreen_spike'"

say "env preflight (dry-run, no browser launched)"
$SSH "SD_SPIKE_OUT='$REMOTE/out' SD_SPIKE_DRYRUN=1 '$REMOTE/run.sh' 0 0" || true
$SSH "grep -E 'PREFLIGHT=|DRYRUN=' '$REMOTE/out/spike.log'"

if [ "$DRYRUN" = "1" ]; then
    $SCP -r "root@192.168.2.15:$REMOTE/out/spike.log" "$DEST/preflight.log" 2>/dev/null || true
    say "dry-run only, exiting (evidence dir: $DEST)"
    exit 0
fi

say "run spike ${W}x${H}"
$SSH "SD_SPIKE_OUT='$REMOTE/out' '$REMOTE/run.sh' '$W' '$H'" || true

say "collect evidence"
$SSH "ls -l '$REMOTE/out'; echo ---; grep -E 'SDWEBVIEW=|WRAPPER=|EXIT_CODE=|AFTERMATH=|PREFLIGHT=RESULT' '$REMOTE/out/spike.log' | head -120"
$SSH "head -40 '$REMOTE/out/procs.log'"
mkdir -p "$DEST"
$SCP -r "root@192.168.2.15:$REMOTE/out/." "$DEST/" || echo "SCP_BACK_FAILED"

say "device aftermath"
$SSH "pgrep -a -f 'wpe-webkit-2.0' | head -5; echo '--- dmesg'; dmesg | tail -15"

say "done: evidence in $DEST"
