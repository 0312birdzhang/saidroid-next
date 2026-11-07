#!/bin/sh
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
echo "===== WPEBackend-default"
$SSH 'ls -la /usr/lib64/libWPEBackend* /usr/lib64/wpe-1.0 2>&1'
echo "===== loader default"
$SSH 'strings /usr/lib64/libwpe-1.0.so.1.10.0 | grep -i -E "WPEBackend|WPE_BACKEND" | head'
echo "===== shm formats"
$SSH 'strings /usr/lib64/libWPEBackend-fdo-1.0.so.1.11.0 | grep -i -E "shm|dmabuf|egl" | head -20'
echo DONE
