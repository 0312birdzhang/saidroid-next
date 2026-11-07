#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH 'echo "--- current lipstick ---"; pgrep -af lipstick | head -3
echo "--- journal lipstick starts (all available) ---"; journalctl --no-pager -o short-iso 2>/dev/null | grep -iE "lipstick|compositor" | grep -iE "start|exec|spawn|kill|signal|coredump" | tail -15
echo "--- evdevtouch error count and first/last ---"; journalctl --no-pager -o short-iso 2>/dev/null | grep -c "evdevtouch"
journalctl --no-pager -o short-iso 2>/dev/null | grep "evdevtouch" | head -3
journalctl --no-pager -o short-iso 2>/dev/null | grep "evdevtouch" | tail -3
echo "--- sdinput devices in dmesg ---"; dmesg 2>/dev/null | grep -i "sdinput" | tail -5
echo "--- journal since ---"; journalctl --no-pager -o short-iso 2>/dev/null | head -1' 2>&1
