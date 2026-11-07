#!/bin/bash
# 抓 CPU 热插拔抖动"开始那一刻"的上下文 + 当前有哪些我们的/安卓的进程在跑。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
OUT=/media/psf/Home/WorkSpace/saidroid-next/build/evidence/deadlock-20261027
mkdir -p "$OUT"
$SSH '
echo "### first_hotplug_ts"; dmesg | grep -n "Booted secondary processor" | head -1
echo "### dmesg_context"
dmesg | awk -F"]" "{t=\$1; gsub(/\[/,\"\",t); ts=t+0; if (ts>162400 && ts<162700) print}" | head -60
echo "### first_wdog"; dmesg | grep -n "wdog_bark" | head -1
echo "### procs_saidroid"; ps -eo pid,etimes,pcpu,rss,comm,args 2>/dev/null | grep -iE "dalvik|saidroid|qq|sdtool|sdinput|hwservicemanager|keymaster|wait_for_strongbox" | grep -v grep
echo "### lipstick_children"; ps --ppid $(pidof lipstick) -o pid,comm 2>/dev/null | head
echo "### nproc_running"; ps -eo stat 2>/dev/null | grep -c "^R"
' > "$OUT/pre-reboot-context.txt" 2>&1
echo SAVED; sed -n 1,70p "$OUT/pre-reboot-context.txt"
