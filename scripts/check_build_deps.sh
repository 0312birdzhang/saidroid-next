#!/bin/bash
echo "=== VM 上的构建依赖 ==="
for t in gcc g++ meson ninja pkg-config make python3 java javac; do
  printf "%-12s " "$t"; which $t 2>/dev/null || echo "-"
done
echo
echo "=== 关键库 ==="
for l in libelf libunwind libbsd liblzma libz; do
  printf "%-12s " "$l"
  pkg-config --exists $l 2>/dev/null && pkg-config --modversion $l || echo "缺"
done
echo
echo "=== 磁盘 ==="
df -h / | tail -1
