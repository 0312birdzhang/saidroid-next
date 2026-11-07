#!/bin/bash
# 重启前抢救 journal（volatile journal 重启即丢）。重点 12:55–13:20 与 lipstick/input/mce。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
OUT=/media/psf/Home/WorkSpace/saidroid-next/build/evidence/deadlock-20261027
mkdir -p "$OUT"
$SSH 'echo "### journal_since"; journalctl --since "-40min" --no-pager 2>/dev/null | tail -200
echo "### journal_lipstick"; journalctl -b --no-pager -u lipstick 2>/dev/null | tail -60
echo "### evdevtouch_count"; journalctl -b --no-pager 2>/dev/null | grep -c "Could not read from input device"
echo "### abend_count"; journalctl -b --no-pager 2>/dev/null | grep -ci "ANOM_ABEND\|sig=11"
echo "### mce_state"; systemctl is-active mce 2>/dev/null; systemctl is-active lipstick 2>/dev/null
' > "$OUT/pre-reboot-journal.txt" 2>&1
echo "SAVED $OUT/pre-reboot-journal.txt"
wc -l "$OUT/pre-reboot-journal.txt"
