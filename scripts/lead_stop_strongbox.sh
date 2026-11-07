#!/bin/bash
# 停掉 wait_for_strongbox 的忙轮询（SIGSTOP，可逆；重启后自动恢复），并记录前后 CPU 证据。
set -u
IP=${IP:-192.168.3.14}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
S="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@$IP"
$S 'h=$(pidof hwservicemanager); w=$(pidof wait_for_strongbox)
echo "before: hw=$h wait=$w"
j(){ awk "{print \$14+\$15}" /proc/$h/stat; }
a=$(j); sleep 10; b=$(j); echo "hwservicemanager 10s 增量(停之前): $((b-a)) jiffies"
kill -STOP $w && echo "STOPPED $w"
sleep 5
c=$(j); sleep 10; d=$(j); echo "hwservicemanager 10s 增量(停之后): $((d-c)) jiffies"
echo "wait 状态: $(awk "{print \$3}" /proc/$w/stat)  (T=已停)"
echo "load: $(cut -d" " -f1-3 /proc/loadavg)"
uptime' 2>&1
