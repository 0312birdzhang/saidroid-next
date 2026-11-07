#!/bin/bash
# 找 lipstick 的 SIGSEGV core：rich-core 的落点 + journal 里两次崩溃的时间线。
# 只读，不上机跑任何应用。在 VM 内按路径执行。
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"

echo "=== rich-core 目录 ==="
$SSH "ls -la /var/lib/rich-core 2>/dev/null | head -20; echo '---'; ls -la /home/defaultuser 2>/dev/null | grep -i -E 'core|rich' | head -10" 2>&1

echo "=== 全盘找 core（限制深度与时间） ==="
$SSH "find / -xdev -maxdepth 6 \( -name 'core*.lipstick*' -o -name '*lipstick*core*' -o -name 'core.*' \) -newermt '-6 hours' 2>/dev/null | head -20" 2>&1

echo "=== journal: lipstick 退出/重启历史（含今天两次） ==="
$SSH "journalctl --no-pager -o short-iso 2>/dev/null | grep -E 'lipstick\[|lipstick.service' | grep -E 'ANOM_ABEND|code=dumped|Scheduled restart|Failed with result|Started|Main process exited' | tail -25" 2>&1

echo "=== journal: 每次崩溃前 60 行里的 evdevtouch / input 相关 ==="
$SSH "journalctl --no-pager -o short-iso -S '-4 hours' 2>/dev/null | grep -E 'evdevtouch|sdinput|Could not read from input' | tail -30" 2>&1

echo "=== 当前 lipstick 与 restart 计数 ==="
$SSH "pgrep -a lipstick | head -5; echo '---'; systemctl --user show lipstick -p NRestarts -p ActiveEnterTimestamp 2>/dev/null; systemctl show lipstick -p NRestarts 2>/dev/null" 2>&1
