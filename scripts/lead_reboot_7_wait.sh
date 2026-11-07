#!/bin/bash
# 等手机真正起来：SSH banner 出现 + 能执行命令。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
for i in $(seq 1 40); do
  b=$(timeout 5 bash -c 'exec 3<>/dev/tcp/bonito/22; head -c 40 <&3' 2>/dev/null | tr -d "\r\n")
  o=$(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 -o NumberOfPasswordPrompts=1 root@bonito 'cut -d" " -f1 /proc/uptime; cat /proc/sys/kernel/random/boot_id' 2>&1 | tr "\n" " ")
  echo "[$i] $(date +%H:%M:%S) banner='${b:0:20}' ssh='${o:0:90}'"
  case "$o" in
    *boot_id*|*[0-9]*" "*) ;;
  esac
  if echo "$o" | grep -qE "^[0-9.]+ [0-9a-f-]{36} $"; then echo "UP"; exit 0; fi
  if [ -n "$b" ] && echo "$o" | grep -q "boot_id"; then echo "UP"; exit 0; fi
  sleep 10
done
echo "STILL_DOWN"
