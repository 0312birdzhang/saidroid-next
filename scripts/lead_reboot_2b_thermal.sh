#!/bin/bash
# 重启前抢救 dmesg / 热 / CPU 在线状态：这些重启后全丢，而"画面卡住"最可能是热降频或 CPU 掉核。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
OUT=/media/psf/Home/WorkSpace/saidroid-next/build/evidence/deadlock-20261027
mkdir -p "$OUT"
$SSH '
echo "### date"; date -Is
echo "### dmesg_tail"; dmesg | tail -40
echo "### cpu_online"; cat /sys/devices/system/cpu/online
echo "### cpu_present"; cat /sys/devices/system/cpu/present
echo "### thermal_zones"
for z in /sys/class/thermal/thermal_zone*; do
  [ -e "$z/temp" ] || continue
  echo "$(basename $z) type=$(cat $z/type 2>/dev/null) temp=$(cat $z/temp 2>/dev/null)"
done
echo "### cooling"
for c in /sys/class/thermal/cooling_device*; do
  [ -e "$c/cur_state" ] || continue
  echo "$(basename $c) type=$(cat $c/type 2>/dev/null) cur=$(cat $c/cur_state 2>/dev/null) max=$(cat $c/max_state 2>/dev/null)"
done
echo "### cpu_freq"
for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do echo "$(dirname $f | xargs basename)=$(cat $f 2>/dev/null)"; done
echo "### journal_head_boot"; journalctl -b --no-pager 2>/dev/null | head -20
echo "### journal_keywords"
journalctl -b --no-pager 2>/dev/null | grep -ciE "thermal|throttl|watchdog|hung task|lowmemory|oom"
echo "### psi"; cat /proc/pressure/cpu 2>/dev/null; cat /proc/pressure/io 2>/dev/null
echo "### androidcpu"; for p in $(pidof hwservicemanager); do set -- $(cut -d" " -f14,15,22 /proc/$p/stat); echo "hwsm pid=$p utime=$1 stime=$2 start=$3"; done
' > "$OUT/pre-reboot-thermal.txt" 2>&1
echo SAVED; wc -l "$OUT/pre-reboot-thermal.txt"
