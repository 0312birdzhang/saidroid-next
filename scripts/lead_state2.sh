#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- procs:'; pgrep -af 'saildroid-supervisor|SdRuntime|wpe-webkit|WPEWeb|spike' 2>/dev/null || echo none; echo '--- usage check:'; /home/art/bin/saildroid-open --help 2>&1 | head -12"
