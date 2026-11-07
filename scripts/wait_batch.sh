#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
for i in $(seq 1 20); do
  sleep 30
  R=$($SSH 'grep -cE "^QB=batch" /tmp/qb.log 2>/dev/null; grep -E "QB=OK|OutOfMemory" /tmp/qb.log 2>/dev/null | tail -1; free -m | awk "NR==2{print \$7}"' 2>/dev/null)
  echo "[$i] $R" | tr '\n' ' '
  echo ""
  echo "$R" | grep -q "QB=OK" && echo "=== 完成 ===" && break
  echo "$R" | grep -q "OutOfMemory" && echo "=== OOM ===" && break
done
$SSH 'tail -8 /tmp/qb.log 2>/dev/null; echo "---"; ls -la /tmp/out/*.jar 2>/dev/null | wc -l; du -sh /tmp/out 2>/dev/null'
