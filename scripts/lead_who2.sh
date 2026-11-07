#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- newest qq log:'; ls -lat /home/art/data/logs/com.tencent.mobileqq/ | head -3; L=\$(ls -t /home/art/data/logs/com.tencent.mobileqq/*.log | head -1); echo \$L; echo '--- perf markers:'; grep -c -i 'perf' \$L 2>/dev/null; grep -m5 -i 'SAILDROID_PERF\|perf_dump\|perf_meta' \$L 2>/dev/null; echo '--- newest test files:'; ls -lat /home/art/test | head -8; echo '--- perf dirs:'; ls -d /var/tmp/*perf* /home/art/test/*perf* 2>/dev/null | head"
