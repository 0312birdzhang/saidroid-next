#!/bin/bash
# 重启前现场取证（在 VM 里跑，通过 ssh 操作手机）。
# 目的：把"死机"现场固化成可比对的数字，重启后逐项复核：
#   1) boot_id / uptime        —— 证明真的重启了
#   2) lipstick pid+start_ticks —— 合成器是否换过
#   3) event1 fd 数量           —— 真触摸屏是否被重复打开
#   4) hwservicemanager jiffies —— HAL 空转是否从开机起就有
#   5) 内存 / swap / disk / load
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
OUT=${1:-/media/psf/Home/WorkSpace/saidroid-next/build/evidence/deadlock-20261027}
mkdir -p "$OUT"

run() { echo "### $1" | tee -a "$OUT/$2"; shift 2; "$@" 2>&1 | tee -a "$OUT/$2"; echo | tee -a "$OUT/$2"; }

CAP="$OUT/pre-reboot.txt"
: > "$CAP"

$SSH '
echo "### boot_id"; cat /proc/sys/kernel/random/boot_id
echo "### uptime_sec"; cut -d" " -f1 /proc/uptime
echo "### date"; date -Is
echo "### lipstick"; for p in $(pidof lipstick); do echo "pid=$p start_ticks=$(cut -d" " -f22 /proc/$p/stat)"; done
echo "### hwservicemanager"; for p in $(pidof hwservicemanager); do set -- $(cut -d" " -f14,15,22 /proc/$p/stat); echo "pid=$p utime=$1 stime=$2 starttime=$3"; done
echo "### keymaster"; for n in keymaster@4.0-service-qti wait_for_strongbox; do for p in $(pidof $n); do set -- $(cut -d" " -f14,15,22 /proc/$p/stat); echo "name=$n pid=$p utime=$1 stime=$2 starttime=$3"; done; done
echo "### loadavg"; cat /proc/loadavg
echo "### mem"; grep -E "^(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree)" /proc/meminfo
echo "### disk"; df -h /home /var/tmp | tail -3
echo "### event_fds"
for p in $(pidof lipstick); do
  n1=$(ls -l /proc/$p/fd 2>/dev/null | grep -c "input/event1")
  n0=$(ls -l /proc/$p/fd 2>/dev/null | grep -c "input/event0")
  n2=$(ls -l /proc/$p/fd 2>/dev/null | grep -c "input/event2")
  echo "lipstick_pid=$p event0=$n0 event1=$n1 event2=$n2"
  ls -l /proc/$p/fd 2>/dev/null | grep "input/event" | sed "s/^/  /"
done
echo "### top5_cpu"
top -b -n 1 -o %CPU 2>/dev/null | head -12
' | tee -a "$CAP"

echo "CAPTURED $CAP"
