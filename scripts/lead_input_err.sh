#!/bin/bash
SSHPASS="${SSHPASS:?Set SSHPASS for device development}" sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'bash -s' <<'REMOTE'
echo "--- press.log ---"; cat /tmp/press.log 2>/dev/null | head -20
echo "--- binaries ---"; ls -l /home/art/test/sdinput /home/art/bin/sdinput 2>&1 | head
echo "--- uinput node ---"; ls -l /dev/uinput 2>&1
echo "--- run directly ---"; /home/art/test/sdinput tap 540 1200 60; echo RC=$?
sleep 1; grep -ac 'sdinput' /proc/bus/input/devices; dmesg | grep -i 'input:' | tail -3
REMOTE
