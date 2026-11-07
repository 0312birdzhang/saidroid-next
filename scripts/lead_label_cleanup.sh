#!/bin/bash
# 清掉与正式 release 重复的 npe* 标签目录和暂存目录，只留 r63 / perf3 / perf6 / r78。
set -eu
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'set -e
for d in /home/art/releases/api29-npe32 /home/art/releases/api29-npe34 /home/art/releases/api29-npe36; do
  [ -d "$d" ] && rm -rf "$d" && echo "REMOVED $d"
done
rm -rf /home/art/test/api29-deploy-* 2>/dev/null || true
echo "--- releases now ---"; ls -1 /home/art/releases/
echo "--- root ---"; readlink /home/art/api29-root
echo "--- df ---"; df -h / | tail -1
echo "--- lock ---"; cat /home/art/test/.device-lock/owner 2>/dev/null || echo LOCK_FREE'
