#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
for i in $(seq 1 24); do
  out=$(sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o NumberOfPasswordPrompts=1 root@bonito 'cat /proc/sys/kernel/random/boot_id; cut -d" " -f1 /proc/uptime' 2>&1)
  rc=$?
  echo "[$i] $(date -Is) rc=$rc out=$(echo "$out" | tr '\n' ' ' | cut -c1-160)"
  if [ $rc -eq 0 ]; then echo "UP"; exit 0; fi
  sleep 10
done
echo "STILL_DOWN"
