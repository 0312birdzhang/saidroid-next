#!/bin/bash
set -e
V=/tmp/sdview
rm -rf $V && mkdir -p $V && cd $V
SRC=/media/psf/Home/.dsh/bot/workspace/sailfish-os/build/viewer
echo "=== 生成 xdg-shell 协议代码 ==="
wayland-scanner client-header /usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml xdg-shell-client-protocol.h
wayland-scanner private-code  /usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml xdg-shell-protocol.c
echo "=== 编译 sdview ==="
gcc -O2 -I$V -o $V/sdview $SRC/sdview.c xdg-shell-protocol.c -lwayland-client 2>&1 | head -10
ls -l $V/sdview
echo "=== 编译 Java 渲染端 ==="
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
DXJAR=/tmp/art-build/art-standalone/out/host/linux-x86/framework/dx.jar
mkdir -p $V/cls
$JAVA/javac --release 8 -nowarn -cp /tmp/fw23/cls -d $V/cls $SRC/RenderFrame.java 2>&1 | grep -v obsolete | head -5
$JAVA/java -cp $DXJAR com.android.dx.command.Main --dex --output=$V/render.dex $V/cls 2>&1 | head -3
ls -l $V/render.dex
