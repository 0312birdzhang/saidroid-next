#!/bin/sh
# Determine SHM init API + libwpe loader env name.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
echo "########## unstable headers"
$SSH 'ls /usr/include/wpe-fdo-1.0/wpe/unstable/ 2>&1'
echo "########## fdo-shm.h"
$SSH 'cat /usr/include/wpe-fdo-1.0/wpe/unstable/fdo-shm.h 2>&1'
echo "########## loader.h"
$SSH 'sed -n 1,120p /usr/include/wpe-1.0/wpe/loader.h 2>&1'
echo "########## egl exported image / extensions"
$SSH 'ls /usr/include/wpe-fdo-1.0/wpe/extensions/ 2>&1'
echo DONE
