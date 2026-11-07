#!/bin/bash
set -eu
SSHPASS="${SSHPASS:?Set SSHPASS for device development}" sshpass -e scp -o StrictHostKeyChecking=no /tmp/sdinput-build/sdinput root@bonito:/home/art/bin/sdinput
SSHPASS="${SSHPASS:?Set SSHPASS for device development}" sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'chmod 755 /home/art/bin/sdinput; ls -l /home/art/bin/sdinput'
