#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@bonito"
OLD="d5dc0013-207f-4940-90fb-e5e23d4514f5"
echo "=== 等待设备重启（旧 boot_id=$OLD）==="
for i in $(seq 1 30); do
  sleep 15
  R=$($SSH 'cat /proc/sys/kernel/random/boot_id 2>/dev/null' 2>/dev/null | tr -d '\r')
  if [ -n "$R" ] && [ "$R" != "$OLD" ]; then
    echo "[$i] 新 boot_id=$R"
    echo "=== 设备已重启 ==="
    $SSH 'uptime; free -m | head -3; df -h /tmp | tail -1' 2>&1 | tail -6
    exit 0
  fi
  echo "[$i] 等待中... (boot_id=${R:-无响应})"
done
echo "=== 超时，检查状态 ==="
ping -c 2 -W 2 bonito 2>&1 | tail -2
