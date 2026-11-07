#!/bin/bash
# 扫描 192.168.2.0/24 里开 22 端口并回 SSH banner 的主机，确认手机是不是换了 IP。
set -u
for i in $(seq 1 254); do
  ip=192.168.2.$i
  ( timeout 1 bash -c "exec 3<>/dev/tcp/$ip/22; head -c 40 <&3" 2>/dev/null | tr -d "\r" | sed "s|^|$ip |" ) &
done
wait
echo "### done"
