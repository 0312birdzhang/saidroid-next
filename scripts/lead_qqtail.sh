#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
LOG=$($SSH "python3 /home/art/bin/sdtool.py status 2>/dev/null | sed -n 's/^log=//p'")
echo "log=$LOG"
$SSH "tail -60 '$LOG'" 2>/dev/null | cut -c1-200
