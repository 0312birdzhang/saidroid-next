#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "A:"; $SSH "pgrep -x lipstick | head -1"
echo "B:"; $SSH "pidof lipstick | cut -d' ' -f1"
echo "C:"; $SSH "awk '{print \$22}' /proc/46884/stat"
