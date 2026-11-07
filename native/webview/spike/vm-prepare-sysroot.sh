#!/bin/sh
# VM-side setup: pull the device's WPE dev headers + link stubs into a private sysroot.
# Read-only on the device; writes only under /var/tmp/sd-webview-spike.
set -eu
SYSROOT=/var/tmp/sd-webview-spike
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=8"

mkdir -p "$SYSROOT/include" "$SYSROOT/lib" "$SYSROOT/log"

if [ ! -d "$SYSROOT/include/wpe-webkit-2.0/wpe" ]; then
  echo "== copying headers"
  $SCP -r root@192.168.2.15:/usr/include/wpe-webkit-2.0 "$SYSROOT/include/"
  $SCP -r root@192.168.2.15:/usr/include/wpe-1.0      "$SYSROOT/include/"
  $SCP -r root@192.168.2.15:/usr/include/wpe-fdo-1.0  "$SYSROOT/include/"
fi

# Link-time stubs: real device libraries (same aarch64/glibc). Only needed for -l resolution.
if [ ! -e "$SYSROOT/lib/libWPEWebKit-2.0.so.1" ]; then
  echo "== copying link libraries (194M)"
  $SCP -p root@192.168.2.15:/usr/lib64/libWPEWebKit-2.0.so.1.11.4 "$SYSROOT/lib/"
  ln -sf libWPEWebKit-2.0.so.1.11.4 "$SYSROOT/lib/libWPEWebKit-2.0.so.1"
  ln -sf libWPEWebKit-2.0.so.1        "$SYSROOT/lib/libWPEWebKit-2.0.so"
fi
if [ ! -e "$SYSROOT/lib/libwpe-1.0.so.1" ]; then
  $SCP -p root@192.168.2.15:/usr/lib64/libwpe-1.0.so.1.10.0 "$SYSROOT/lib/"
  ln -sf libwpe-1.0.so.1.10.0 "$SYSROOT/lib/libwpe-1.0.so.1"
  ln -sf libwpe-1.0.so.1      "$SYSROOT/lib/libwpe-1.0.so"
fi
if [ ! -e "$SYSROOT/lib/libWPEBackend-fdo-1.0.so.1" ]; then
  $SCP -p root@192.168.2.15:/usr/lib64/libWPEBackend-fdo-1.0.so.1.11.0 "$SYSROOT/lib/"
  ln -sf libWPEBackend-fdo-1.0.so.1.11.0 "$SYSROOT/lib/libWPEBackend-fdo-1.0.so.1"
  ln -sf libWPEBackend-fdo-1.0.so.1      "$SYSROOT/lib/libWPEBackend-fdo-1.0.so"
fi

echo "== sysroot"
ls -l "$SYSROOT/lib"
du -sh "$SYSROOT/include"
