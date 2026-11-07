#!/bin/bash
set -u
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
W=/tmp/ap
python3 /media/psf/Home/WorkSpace/saidroid-next/scripts/debug/genstub.py \
  --javap $JAVA/javap --cp /tmp/fw23/cls \
  --iface android.view.IWindowManager --class SdWindowManagerService \
  --out $W/SdWindowManagerService.java \
  --comment "系统级方法里只有动画缩放、初始显示尺寸/密度需要真值，其余在无窗口场景不会被调用"
echo "=== 生成结果 ==="
head -12 $W/SdWindowManagerService.java
wc -l $W/SdWindowManagerService.java
