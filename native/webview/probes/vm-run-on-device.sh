#!/bin/sh
# Generic helper: copy a probe script to the device and run it there.
# Usage: vm-run-on-device.sh <local probe script> [out file]
# Exists because `prlctl exec 'MeeGo Build' sh -c '...'` re-splits the command line
# and destroys quoting; anything non-trivial must be a script file.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
SRC="$1"
OUT="${2:-}"
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
O="-o StrictHostKeyChecking=no -o ConnectTimeout=8"
sshpass -e ssh $O root@192.168.2.15 'echo DEVICE_OK' >/dev/null
sshpass -e ssh $O root@192.168.2.15 "cat > /tmp/probe.sh" < "$SRC"
if [ -n "$OUT" ]; then
    sshpass -e ssh $O root@192.168.2.15 'sh /tmp/probe.sh' > "$OUT" 2>&1 || true
    echo "OUT=$OUT lines=$(wc -l < "$OUT")"
    cat "$OUT"
else
    sshpass -e ssh $O root@192.168.2.15 'sh /tmp/probe.sh' 2>&1
fi
