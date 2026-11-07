#!/bin/bash
sshpass -e ssh -o StrictHostKeyChecking=no root@bonito \
'echo "=== 设备内存 ==="; free -m | head -3
echo "=== /tmp 空间 ==="; df -h /tmp | tail -1
echo "=== 总存储 ==="; df -h / | tail -1' 2>&1 | tail -10
