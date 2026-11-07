#!/bin/sh
# Dump input dispatch API + egl exportable variant header.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
echo "########## view-backend-exportable-egl.h"
$SSH "cat /usr/include/wpe-fdo-1.0/wpe/view-backend-exportable-egl.h" 2>&1
echo "########## input.h structs+dispatch"
$SSH "grep -n -E 'struct wpe_input_|wpe_input_.*event|dispatch' /usr/include/wpe-1.0/wpe/input.h" 2>&1 | head -80
echo "########## view-backend.h dispatch decls"
$SSH "grep -n -E 'dispatch|set_size|set_visible|set_focus' /usr/include/wpe-1.0/wpe/view-backend.h" 2>&1
echo "########## wayland-client headers on device"
$SSH "ls /usr/include/wayland-client*.h /usr/include/wayland-client-protocol.h 2>&1"
echo "########## wayland libs"
$SSH "ls -l /usr/lib64/libwayland-client.so* /usr/lib64/libwayland-server.so* 2>&1"
echo "########## glib main"
$SSH "ls /usr/include/glib-2.0/glib.h 2>&1"
echo "DONE"
