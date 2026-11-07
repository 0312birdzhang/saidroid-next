#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "ls -la /home/art/test/.device-lock/ 2>&1; echo '--- owner:'; cat /home/art/test/.device-lock/owner 2>&1; echo '--- now:'; date +%s; echo '--- art procs:'; pgrep -af 'saildroid|SdRuntime|wpe-webkit|WPEWeb' 2>/dev/null || echo none"
