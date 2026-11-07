#!/bin/bash
echo "=== VM 架构 ==="
uname -m
uname -a
echo
echo "=== 编译器目标 ==="
gcc -dumpmachine
echo
echo "=== 是否有多架构支持 ==="
ls /usr/bin/*-gcc 2>/dev/null | head -5
echo
echo "=== art_standalone 的 ARCH 处理 ==="
cd /tmp/art-standalone 2>/dev/null && grep -n "ARCH" Makefile 2>/dev/null | head -10
