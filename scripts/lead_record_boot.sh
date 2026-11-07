#!/bin/bash
# 设备重启后 boot_id 会变，而部署/校验脚本用它当"别在重启过的机器上悄悄装东西"的
# 防线。重启后跑一次本脚本，把设备当前 boot_id 同步进所有脚本（docs 里的历史值不动）。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
REPO=/media/psf/Home/WorkSpace/saidroid-next
NEW=$(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito \
      'cat /proc/sys/kernel/random/boot_id' 2>/dev/null) || exit 3
[ ${#NEW} -eq 36 ] || { echo "BAD_BOOT_ID=$NEW"; exit 4; }
OLD=$(grep -hoE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' \
      "$REPO/scripts/api29/deploy-component.py" | head -1)
[ -n "$OLD" ] || { echo "NO_BASELINE_FOUND"; exit 5; }
[ "$OLD" = "$NEW" ] && { echo "BOOT_ID_UNCHANGED=$NEW"; exit 0; }
grep -rl -- "$OLD" "$REPO/scripts" --include='*.py' --include='*.sh' 2>/dev/null | while read -r f; do
  sed -i "s/$OLD/$NEW/g" "$f"
done
echo "BOOT_ID_BASELINE=$NEW"
echo "BOOT_ID_PREVIOUS=$OLD"
