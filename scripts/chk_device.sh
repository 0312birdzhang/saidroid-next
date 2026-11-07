#!/bin/bash
echo "=== ping ==="
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito 'echo ALIVE; uptime; free -m | head -2' 2>&1 | tail -6
