#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "=== 1. SSH 是否响应 ==="
$SSH 'echo ALIVE; uptime; free -m | head -3' 2>&1 | tail -6
echo
echo "=== 2. 立即杀掉所有 java 进程 ==="
$SSH 'pkill -9 -f "java -Xmx" 2>/dev/null; pkill -9 java 2>/dev/null; echo KILLED' 2>&1 | tail -2
echo
echo "=== 3. 删除 /tmp 里的大文件 ==="
$SSH 'rm -rf /tmp/out /tmp/qqdex /tmp/*.jar /tmp/*.class 2>/dev/null; df -h /tmp | tail -1; free -m | head -2' 2>&1 | tail -4
