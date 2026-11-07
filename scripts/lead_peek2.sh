#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "cat /home/art/test/.device-lock/owner 2>/dev/null; echo ---; pidof lipstick; echo ---; ls /home/defaultuser/Downloads/SailDroid-Screenshots/ 2>/dev/null | tail -4; echo ---; date"
