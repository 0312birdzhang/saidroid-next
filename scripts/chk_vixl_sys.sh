#!/bin/bash
echo "=== 系统有 vixl 吗 ==="
ls /usr/lib/*/libvixl* /usr/lib/libvixl* 2>/dev/null
pkg-config --exists vixl 2>/dev/null && echo "pkg-config: $(pkg-config --modversion vixl)" || echo "pkg-config: 无"
echo "=== 头文件 ==="
ls /usr/include/aarch64/disasm-aarch64.h 2>/dev/null || echo "无头文件"
echo
echo "=== 仓库里的 vixl 引用（是否有 submodule 配置）==="
cd /tmp/art-build/art-standalone
cat .gitmodules 2>/dev/null | head -10 || echo "无 .gitmodules"
echo
echo "=== README 是否提 vixl ==="
grep -i "vixl" README.md 2>/dev/null | head -5
