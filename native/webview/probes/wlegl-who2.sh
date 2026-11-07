#!/bin/sh
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
echo "== /usr/libexec/droid-hybris tree"
$SSH "find /usr/libexec/droid-hybris -maxdepth 3 2>/dev/null | head -30"
echo
echo "== strings in droid-hybris binaries mentioning wlegl / gralloc"
$SSH "for f in \$(find /usr/libexec/droid-hybris -type f 2>/dev/null | head -20); do strings -a \"\$f\" 2>/dev/null | grep -i -q 'android_wlegl' && echo \"HIT \$f\"; done; echo done"
echo
echo "== lipstick plugins / QML: any wayland extension registration"
$SSH "ls /usr/lib64/lipstick 2>/dev/null | head; strings -a /usr/bin/lipstick | grep -i -E 'wl_global_create|zwp_|org_kde' | head -10"
echo
echo "== does the compositor advertise any private globals? (wayland-info?)"
$SSH "command -v wayland-info weston-info 2>/dev/null; ls /usr/bin | grep -i -E 'wayland|wldebug' | head"
