#!/bin/sh
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
$SSH 'sed -n 55,160p /usr/include/wpe-1.0/wpe/input.h'
