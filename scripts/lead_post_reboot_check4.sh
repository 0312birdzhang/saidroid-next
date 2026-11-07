#!/bin/bash
set -u
IP=${IP:-192.168.3.14}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
S="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@$IP"
echo "=== 自开机累计 CPU 排行 top12"
$S 'awk "{n=split(\$0,a,\")\"); comm=\$2; u=\$14; s=\$15; printf \"%d %s %s\n\", u+s, \$1, comm}" /proc/[0-9]*/stat 2>/dev/null | sort -rn | head -12' 2>&1
echo "=== 10 秒内 CPU 增量 top12（两次快照）"
$S 'snap(){ awk "{u=\$14; s=\$15; printf \"%d %s\n\", u+s, \$1}" /proc/[0-9]*/stat 2>/dev/null; }; snap > /tmp/a; sleep 10; snap > /tmp/b; join /tmp/a /tmp/b -j 2 2>/dev/null | awk "{d=\$3-\$2; if(d>0) printf \"%d jiffies %.1fs %s\n\", d, d/100, \$1}" | sort -rn | head -12' 2>&1
echo "=== strongbox/keymaster 相关进程"
$S 'ps -ef | grep -iE "strongbox|keymaster|hwservice" | grep -v grep' 2>&1
