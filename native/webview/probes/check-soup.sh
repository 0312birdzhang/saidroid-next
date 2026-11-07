#!/bin/sh
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
$SSH 'ls /usr/include/libsoup-3.0/libsoup/ 2>&1 | head -5; ls /usr/include/libsoup-3.0/ 2>&1'
