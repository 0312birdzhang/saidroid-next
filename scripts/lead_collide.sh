#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '=== qq log head:'; head -12 /home/art/data/logs/com.tencent.mobileqq/20261027T050101-47506.log; echo '=== qq log tail:'; tail -12 /home/art/data/logs/com.tencent.mobileqq/20261027T050101-47506.log; echo '=== webview-diag:'; ls -la /home/art/test/webview-diag/ /home/art/test/webview-spike/ 2>&1 | head -20; echo '=== diag1.sh head:'; head -20 /home/art/test/diag1.sh 2>&1"
