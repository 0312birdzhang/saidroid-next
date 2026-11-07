#!/bin/bash
echo "=== USB 设备 ==="
lsusb 2>/dev/null | grep -i pixel
echo "=== RNDIS 接口 ==="
ip -brief addr 2>/dev/null | grep enx
echo "=== ping 手机 ==="
ping -c 2 -W 2 bonito 2>&1 | tail -3
echo "=== 2323 端口 ==="
timeout 5 bash -c 'echo > /dev/tcp/bonito/2323' 2>/dev/null && echo "2323 OPEN" || echo "2323 CLOSED"
