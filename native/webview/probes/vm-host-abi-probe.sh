#!/bin/sh
# Push host-abi-probe.sh to the device (read-only) and pull the two interesting libs
# into the VM for offline symbol/string work. No lock is taken: nothing is executed
# on the device beyond read-only tools.
set -eu
REPO=/media/psf/Home/WorkSpace/saidroid-next
OUT="$REPO/build/codex-api29/webview-hostabi"
COPY=/var/tmp/sd-hostabi
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
O="-o StrictHostKeyChecking=no -o ConnectTimeout=8"

mkdir -p "$OUT" "$COPY"
sshpass -e ssh $O root@192.168.2.15 'echo DEVICE_OK' >/dev/null
echo "DEVICE_OK"

# Capture the read-only survey on the device itself (fast tools only).
sshpass -e ssh $O root@192.168.2.15 "cat > /tmp/host-abi-probe.sh" \
    < "$REPO/native/webview/probes/host-abi-probe.sh"
sshpass -e ssh $O root@192.168.2.15 'sh /tmp/host-abi-probe.sh' > "$OUT/probe.log" 2>&1 || true
echo "PROBE_PULLED $(wc -l < "$OUT/probe.log") lines"

# Pull the small libs for offline strings/objdump. libsailfishbrowser may be large;
# copy only if under 40 MB to keep device I/O light while Lead is diagnosing.
SZ=$(sshpass -e ssh $O root@192.168.2.15 'stat -c %s /usr/lib64/libsailfishbrowser.so.1 2>/dev/null || echo 0')
echo "SAILFISHBROWSER_SIZE=$SZ"
if [ "${SZ:-0}" -lt 40000000 ]; then
    sshpass -e scp $O root@192.168.2.15:/usr/lib64/libsailfishbrowser.so.1 "$COPY/" >/dev/null
else
    echo "SKIP_COPY_TOO_BIG"
fi
sshpass -e scp $O root@192.168.2.15:/usr/lib64/wpe-compat/libegl-stubs.so "$COPY/" >/dev/null 2>&1 || echo "STUB_COPY_FAIL"
ls -l "$COPY" | sed 's/^/   /'
