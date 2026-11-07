#!/bin/bash
# 等设备锁释放（最多 $1 秒），打印最终状态。用于 Lead 的令牌调度。
LIMIT=${1:-240}
for i in $(seq 1 $((LIMIT/10))); do
  s=$(prlctl exec "MeeGo Build" "/bin/bash /media/psf/Home/WorkSpace/saidroid-next/scripts/devlock.sh status" 2>/dev/null | tr -d '\r' | grep -E 'LOCK_' | head -1)
  echo "[$((i*10))s] $s"
  case "$s" in
    LOCK_FREE*) echo "RESULT=FREE"; exit 0 ;;
    LOCK_UNKNOWN*) echo "RESULT=UNKNOWN"; exit 2 ;;
  esac
  sleep 10
done
echo "RESULT=TIMEOUT"
exit 1
