#!/bin/sh
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@192.168.2.15"
WK=/usr/lib64/libWPEWebKit-2.0.so.1.11.4
echo "== env knobs: software/disable GL, cpu render, headless"
$SSH "strings -a $WK | grep -E '^[A-Z][A-Z0-9_]{6,}$' | grep -E 'CPU|SOFTWARE|SOFT|HEADLESS|NO_GL|DISABLE_GL|SKIA|PAINT' | sort -u"
echo
echo "== getenv-style WEBKIT_ vars total count + list (first 120)"
$SSH "strings -a $WK | grep -E '^WEBKIT_[A-Z0-9_]+$' | sort -u | wc -l; strings -a $WK | grep -E '^WEBKIT_[A-Z0-9_]+$' | sort -u | head -120"
echo
echo "== android_wlegl: who provides it (lipstick / libhybris / wayland modules)"
$SSH "grep -rl 'android_wlegl' /usr/lib64 /usr/libexec /usr/bin 2>/dev/null | head -20"
echo
echo "== lipstick/wayland-compositor: env or plugin gating android_wlegl"
$SSH "for f in /usr/bin/lipstick /usr/lib64/libwayland-server.so.0 /usr/lib64/libhybris/eglplatform_wayland.so; do echo \"-- \$f\"; strings -a \"\$f\" 2>/dev/null | grep -i 'android_wlegl' | head -3; done"
