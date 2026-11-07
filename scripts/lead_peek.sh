#!/bin/bash
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
echo "-- root --"; $SSH 'readlink /home/art/api29-root'
echo "-- releases --"; $SSH 'ls -1 /home/art/releases/'
echo "-- lock --"; $SSH 'cat /home/art/test/.device-lock/owner 2>/dev/null || echo FREE'
echo "-- procs --"; $SSH 'pgrep -af "saildroid|WPEWebProcess|deploy-component|vm-run-drawdiag" | head -6 || echo NONE'
echo "-- lock age --"; $SSH 'date +%s'
