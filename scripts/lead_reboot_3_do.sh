#!/bin/bash
# 重启手机并等它回来。判据：ssh 断开 → 重新可登录 → boot_id 变化。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 -o BatchMode=no $H"
OUT=/media/psf/Home/WorkSpace/saidroid-next/build/evidence/deadlock-20261027
mkdir -p "$OUT"
OLD=$($SSH 'cat /proc/sys/kernel/random/boot_id' 2>/dev/null)
echo "OLD_BOOT_ID=$OLD"
echo "REBOOT_ISSUED=$(date -Is)"
$SSH 'sync; (sleep 1; reboot) >/dev/null 2>&1 &' 2>/dev/null || true
sleep 5
# 等断线
for i in $(seq 1 40); do
  if ! $SSH 'true' >/dev/null 2>&1; then echo "LINK_DOWN_AT=$(date -Is) after ${i}0s"; break; fi
  sleep 10
done
# 等回来（最长 6 分钟）
for i in $(seq 1 36); do
  sleep 10
  if $SSH 'true' >/dev/null 2>&1; then
    NEW=$($SSH 'cat /proc/sys/kernel/random/boot_id' 2>/dev/null)
    echo "LINK_UP_AT=$(date -Is) after ${i}0s"
    echo "NEW_BOOT_ID=$NEW"
    [ "$OLD" != "$NEW" ] && echo "REBOOT_CONFIRMED=yes" || echo "REBOOT_CONFIRMED=no"
    exit 0
  fi
done
echo "REBOOT_TIMEOUT=yes"
exit 1
