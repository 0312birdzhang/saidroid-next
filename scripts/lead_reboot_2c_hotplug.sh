#!/bin/bash
# 量化 CPU 热插拔抖动：dmesg 里 secondary processor 的启动次数与时间分布。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
OUT=/media/psf/Home/WorkSpace/saidroid-next/build/evidence/deadlock-20261027
mkdir -p "$OUT"
$SSH '
echo "### count_booted"; dmesg | grep -c "Booted secondary processor"
echo "### first_last"; dmesg | grep "Booted secondary processor" | head -3; dmesg | grep "Booted secondary processor" | tail -3
echo "### per_cpu"; dmesg | grep -o "CPU[0-7]: Booted secondary processor" | sort | uniq -c
echo "### per_minute_last60"; dmesg | grep "Booted secondary processor" | awk "{print \$1}" | sed "s/\[//;s/\]//" | awk "{printf \"%.0f\n\", \$1/60}" | tail -300 | sort -n | uniq -c | tail -15
echo "### wdog_bark"; dmesg | grep -c "wdog_bark"; dmesg | grep "wdog_bark" | tail -5
echo "### online_now"; cat /sys/devices/system/cpu/online
' > "$OUT/pre-reboot-hotplug.txt" 2>&1
echo SAVED; cat "$OUT/pre-reboot-hotplug.txt"
