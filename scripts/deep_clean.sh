#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
echo "=== 检查残留大文件 ==="
$SSH 'du -sh /tmp/* 2>/dev/null | sort -rh | head -8' 2>&1 | tail -10
echo
echo "=== 检查 java 进程 ==="
$SSH 'ps aux 2>/dev/null | grep -E "java|jdk" | grep -v grep | head -5' 2>&1 | tail -6
echo
echo "=== 清理 swap ==="
$SSH 'sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null; swapoff -a 2>/dev/null && swapon -a 2>/dev/null; free -m | head -3' 2>&1 | tail -5
