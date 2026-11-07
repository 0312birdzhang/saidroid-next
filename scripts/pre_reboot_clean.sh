#!/bin/bash
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
echo "=== 重启前清理 ==="
$SSH 'rm -rf /tmp/qq.apk /tmp/jdk /tmp/out /tmp/qqdex /tmp/*.jar /tmp/*.class /tmp/*.java /tmp/org /tmp/com /tmp/hs_err_* /tmp/hsperfdata_* /tmp/libc_full.so 2>/dev/null
echo "CLEANED"
df -h /tmp | tail -1
free -m | head -3' 2>&1 | tail -8
