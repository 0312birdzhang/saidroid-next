#!/bin/bash
# Runs ON the phone. r80 evidence 5: the third wl_shm buffer must not leak.
set -u
TOOL=/home/art/bin/sdtool.py
PKG=org.example.saildroid.perfscroll
findpid(){ for p in /proc/[0-9]*; do [ -r "$p/cmdline" ] || continue; c=$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null); case "$c" in *"$PKG"*) echo "${p#/proc/}";; esac; done | head -1; }
rss(){ awk '/^VmRSS:/{print $2}' "/proc/$1/status" 2>/dev/null; }
python3 "$TOOL" --package "$PKG" close >/dev/null 2>&1
sleep 1
echo "PRE_LAUNCH_PID=$(findpid)"
python3 "$TOOL" --package "$PKG" launch --wait 8 > /tmp/r80-rss-launch.log 2>&1
tail -2 /tmp/r80-rss-launch.log
P=$(findpid); echo "RSS_PID=$P"
sleep 2;  echo "RSS_T2_KB=$(rss "$P")"
sleep 10; echo "RSS_T12_KB=$(rss "$P")"
echo "SHM_FILES=$(ls /dev/shm 2>/dev/null | wc -l)"
python3 "$TOOL" --package "$PKG" close >/dev/null 2>&1
sleep 3
echo "AFTER_CLOSE_PID=$(findpid)"
echo "AFTER_CLOSE_RSS_KB=$(rss "$P")"
