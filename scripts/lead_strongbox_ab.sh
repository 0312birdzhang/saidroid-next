#!/bin/bash
# 可逆实验：SIGSTOP wait_for_strongbox 20s，看 hwservicemanager 的 CPU 是否停止增长，然后 SIGCONT 恢复。
set -u
IP=${IP:-192.168.3.14}
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
S="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 -o NumberOfPasswordPrompts=1 root@$IP"
$S 'h=$(pidof hwservicemanager); w=$(pidof wait_for_strongbox)
j(){ awk "{print \$14+\$15}" /proc/$h/stat; }
echo "hw=$h wait=$w"
a=$(j); sleep 20; b=$(j); echo "BASELINE 20s: $((b-a)) jiffies = $(( (b-a) ))%/s/100"
kill -STOP $w; echo "STOPPED $w"
c=$(j); sleep 20; d=$(j); echo "STOPPED 20s: $((d-c)) jiffies"
kill -CONT $w; echo "CONTINUED $w"
e=$(j); sleep 20; f=$(j); echo "AFTER 20s: $((f-e)) jiffies"
echo "wait_for_strongbox 状态: $(awk "{print \$3}" /proc/$w/stat)"' 2>&1
