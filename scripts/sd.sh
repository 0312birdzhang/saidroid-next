#!/bin/bash
# SailDroid 设备操作入口（在 VM 里跑，通过 ssh 操作手机）。
#
#   sd.sh status | log [-n N] | launch [--wait N] | wait [--wait N] [--marker TXT] | close
#   sd.sh shot <名字>        # 截图并回传到 Mac 仓库 build/screens/
#   sd.sh sync              # 只同步 sdtool.py 到手机
#
# 所有命令都带 --package，默认 com.tencent.mobileqq；用 SD_PKG 覆盖。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=8"
REPO=/media/psf/Home/WorkSpace/saidroid-next
DEVTOOL=/home/art/bin/sdtool.py
PKG=${SD_PKG:-com.tencent.mobileqq}

sync_tool() {
  $SSH "mkdir -p /home/art/bin" >/dev/null 2>&1
  $SCP -q "$REPO/scripts/sdtool.py" "$H:$DEVTOOL"
  $SSH "chmod 755 $DEVTOOL"
}

cmd=${1:-status}
shift || true

case "$cmd" in
sync)
  sync_tool && echo "SYNCED $DEVTOOL"
  ;;
shot)
  name=${1:?用法: sd.sh shot <名字>}
  sync_tool
  out=$($SSH "python3 $DEVTOOL --package $PKG shot $name" 2>&1)
  echo "$out"
  case "$out" in
    SHOT_OK*)
      mkdir -p "$REPO/build/screens"
      $SCP -q "$H:/home/defaultuser/Downloads/SailDroid-Screenshots/$name.png" \
        "$REPO/build/screens/$name.png" && \
        echo "PULLED $REPO/build/screens/$name.png"
      ;;
  esac
  ;;
input|inputseq|inputserve|inputhold)
  # 触摸手势注入：sd.sh input tap X Y / swipe X1 Y1 X2 Y2 [时长ms] [步数]
  # 多步请用：sd.sh inputseq 'tap 791 1900; tap 1005 152; tap 400 1803'
  # 整段脚本：sd.sh inputserve /path/to/steps.txt   ← 一个 uinput 设备跑完，最省热插拔
  # 只测热插拔：sd.sh inputhold 3000               ← 建了就拆，不发事件
  # 二进制按 sha 比对推送，不再是"存在就跳过"——设备上那份曾长期是旧版。
  local_bin=/tmp/sdinput-build/sdinput
  mkdir -p /tmp/sdinput-build
  # 源码改了但二进制是旧的，比"设备上是不是有文件"更要紧：这里每次都按源码重编。
  if [ ! -x "$local_bin" ] || [ "$REPO/scripts/input/sdinput.c" -nt "$local_bin" ]; then
    gcc -O2 -Wall -o "$local_bin" "$REPO/scripts/input/sdinput.c" 2>&1 | head -5
  fi
  if [ -x "$local_bin" ]; then
    lsum=$(sha256sum "$local_bin" | cut -d' ' -f1)
    rsum=$($SSH "sha256sum /home/art/bin/sdinput 2>/dev/null | cut -d' ' -f1")
    if [ "$lsum" != "$rsum" ]; then
      $SSH "mkdir -p /home/art/bin" >/dev/null 2>&1
      $SCP -q "$local_bin" "$H:/home/art/bin/sdinput"
      $SSH "chmod 755 /home/art/bin/sdinput"
      echo "SDINPUT_PUSHED sha256=$lsum"
    fi
  fi
  case "$cmd" in
    inputseq)  $SSH "/home/art/bin/sdinput seq '$*'" ;;
    inputhold) $SSH "/home/art/bin/sdinput hold ${1:-3000}" ;;
    inputserve)
      # stdin 是一段动作脚本（每行一条 tap/swipe/press/sleep，可 # 注释），
      # 整段只建一个 uinput 设备。
      $SSH "/home/art/bin/sdinput serve" < "${1:?用法: sd.sh inputserve <脚本文件>}"
      ;;
    *)         $SSH "/home/art/bin/sdinput $*" ;;
  esac
  ;;
*)
  sync_tool
  $SSH "python3 $DEVTOOL --package $PKG $cmd $*"
  ;;
esac
