#!/bin/sh
# Dump exact WPE fdo exportable API surface.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
for f in view-backend-exportable.h exported-buffer-shm.h exported-image-egl.h initialize-egl.h fdo-egl.h; do
  echo "########## $f"
  $SSH "sed -n '1,200p' /usr/include/wpe-fdo-1.0/wpe/$f" 2>&1
done
echo "########## libwpe renderer-backend-egl.h"
$SSH "sed -n '1,160p' /usr/include/wpe-1.0/wpe/renderer-backend-egl.h" 2>&1
echo "########## libwpe view-backend.h"
$SSH "sed -n '40,120p' /usr/include/wpe-1.0/wpe/view-backend.h" 2>&1
echo "DONE"
