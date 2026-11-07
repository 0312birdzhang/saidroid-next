#!/bin/bash
# 用仓库里的 native/viewer/sdview.c 构建看图器（带 --evfile / --watch）
set -eu
V=/tmp/sdview2
rm -rf $V && mkdir -p $V && cd $V
SRC=/media/psf/Home/WorkSpace/saidroid-next/native/viewer/sdview.c
wayland-scanner client-header /usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml xdg-shell-client-protocol.h
wayland-scanner private-code  /usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml xdg-shell-protocol.c
gcc -O2 -I$V -o $V/sdview $SRC xdg-shell-protocol.c -lwayland-client 2>&1 | head -15
ls -l $V/sdview
cp -f $SRC /media/psf/Home/WorkSpace/saidroid-next/native/viewer/sdview.c
