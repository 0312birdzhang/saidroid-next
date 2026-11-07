#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '=== newest in /home/art/test:'; ls -lat /home/art/test | head -12; echo '=== perf files:'; find /home/art /var/tmp -maxdepth 3 -name '*perf*' -newermt '-40 minutes' 2>/dev/null | head -20; echo '=== qq logs:'; ls -lat /home/art/data/logs/com.tencent.mobileqq/ 2>/dev/null | head -5; echo '=== screenshots:'; ls -lat /home/defaultuser/Downloads/SailDroid-Screenshots/ 2>/dev/null | head -8; echo '=== spike:'; ls -lat /home/art/test/spike* /home/art/test/wpe* 2>/dev/null | head -10"
