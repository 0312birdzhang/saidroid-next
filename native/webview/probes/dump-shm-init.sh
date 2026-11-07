#!/bin/sh
# Confirm SHM init signature, backend env var, helper ELF linkage.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
echo "########## initialize-shm.h"
$SSH 'sed -n 25,80p /usr/include/wpe-fdo-1.0/wpe/unstable/initialize-shm.h' 2>&1
echo "########## initialize-dmabuf.h"
$SSH 'sed -n 25,80p /usr/include/wpe-fdo-1.0/wpe/unstable/initialize-dmabuf.h' 2>&1
echo "########## libwpe env strings"
$SSH 'strings /usr/lib64/libwpe-1.0.so.1.10.0 | grep -E "WPE_|libWPE" ' 2>&1
echo "########## helper type/deps"
$SSH 'file /usr/libexec/wpe-webkit-2.0/WPEWebProcess; readelf -d /usr/libexec/wpe-webkit-2.0/WPEWebProcess | grep -E "NEEDED|RPATH|RUNPATH"; readelf -d /usr/libexec/wpe-webkit-2.0/WPENetworkProcess | grep -E "NEEDED|RPATH|RUNPATH"' 2>&1
echo "########## libWPEWebKit rpath"
$SSH 'readelf -d /usr/lib64/libWPEWebKit-2.0.so.1.11.4 | grep -E "RPATH|RUNPATH"' 2>&1
echo "########## wpe process env defaults"
$SSH 'strings /usr/lib64/libWPEWebKit-2.0.so.1.11.4 | grep -E "WEBKIT_(EXEC|FORCE|DISABLE)_?[A-Z_]*" | sort -u | head -30' 2>&1
echo DONE
