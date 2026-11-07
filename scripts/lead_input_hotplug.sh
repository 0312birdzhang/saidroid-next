#!/bin/bash
SSHPASS="${SSHPASS:?Set SSHPASS for device development}" sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'bash -s' <<'REMOTE'
set -u
LIP=$(pgrep -f '/usr/bin/lipstick' | head -1); echo "lipstick=$LIP"
echo "fds_before: $(ls -l /proc/$LIP/fd 2>/dev/null | grep -o 'event[0-9]*' | sort -u | tr '\n' ' ')"
( /home/art/bin/sdinput press 540 1200 9000 >/tmp/press.log 2>&1 & )
sleep 1.5
echo "devices_now:"; grep -a '^N: Name="sdinput"' /proc/bus/input/devices
echo "input_nodes: $(ls /dev/input/ | tr '\n' ' ')"
echo "fds_during: $(ls -l /proc/$LIP/fd 2>/dev/null | grep -o 'event[0-9]*' | sort -u | tr '\n' ' ')"
sleep 2
echo "fds_later: $(ls -l /proc/$LIP/fd 2>/dev/null | grep -o 'event[0-9]*' | sort -u | tr '\n' ' ')"
echo "--- press.log ---"; cat /tmp/press.log | head -5
REMOTE
