#!/bin/bash
echo "=== USB 设备 ==="
lsusb 2>/dev/null | grep -iE "pixel|18d1"
echo "=== RNDIS 接口 ==="
ip -brief addr 2>/dev/null | grep enx
echo "=== 路由 ==="
ip route 2>/dev/null | grep 192.168.2
echo "=== 2323 端口（init-debug shell）==="
timeout 5 bash -c 'echo > /dev/tcp/bonito/2323' 2>/dev/null && echo "2323 OPEN" || echo "2323 CLOSED"
echo "=== 22 端口（SSH）==="
timeout 5 bash -c 'echo > /dev/tcp/bonito/22' 2>/dev/null && echo "22 OPEN" || echo "22 CLOSED"
