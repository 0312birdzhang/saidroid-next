#!/bin/sh
# Read-only: who can advertise the hybris `android_wlegl` Wayland global?
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
echo "== lipstick binary: android_wlegl strings"
$SSH "ls -l /usr/bin/lipstick; strings -a /usr/bin/lipstick 2>/dev/null | grep -i 'android_wlegl' | head -10"
echo
echo "== libs likely to implement it (targeted, no -r over /usr/lib64)"
$SSH "for f in /usr/lib64/libhybris/libwayland-android-wlegl.so* /usr/lib64/libwayland-android*.so* /usr/lib64/libhybris-common.so.1 /usr/lib64/libhardware.so.2; do [ -e \"\$f\" ] && { echo \"-- \$f\"; strings -a \"\$f\" | grep -i 'android_wlegl' | head -5; }; done"
echo
echo "== any installed file with the protocol name (targeted dirs)"
$SSH "ls /usr/lib64/ | grep -i -E 'wlegl|android' | head -20; echo '---'; ls /usr/libexec 2>/dev/null | head -20"
echo
echo "== lipstick cmdline + env (how it is started)"
$SSH "cat /proc/\$(pgrep -f '^/usr/bin/lipstick' | head -1)/cmdline 2>/dev/null | tr '\0' ' '; echo; grep -o 'android[^ ,]*' /proc/\$(pgrep -f '^/usr/bin/lipstick' | head -1)/environ 2>/dev/null | head"
echo
echo "== is there a wayland-scanner protocol xml for it?"
$SSH "ls /usr/share/wayland* /usr/share/*/wayland* 2>/dev/null | head -20"
