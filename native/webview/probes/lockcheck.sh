#!/bin/sh
# Read-only: is someone else holding the device lock, and are OUR leftovers alive?
# pgrep -f patterns use [w]/[ ] bracket trick so they do not match this script's own
# command line (which is why an earlier run reported 2 phantom processes).
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
O="-o StrictHostKeyChecking=no -o ConnectTimeout=6"
sshpass -e ssh $O root@192.168.2.15 '
if [ -d /home/art/test/.device-lock ]; then echo "LOCK_HELD $(cat /home/art/test/.device-lock/owner 2>/dev/null)"; else echo LOCK_FREE; fi
echo "SPIKE_PROCS=$(pgrep -f "[w]pe_offscreen_spike" | wc -l)"
echo "WPE_PROCS=$(pgrep -f "[w]pe-webkit-2\\.0" | wc -l)"
[ "$(pgrep -f "[w]pe_offscreen_spike" | wc -l)" -gt 0 ] && ps -o pid,ppid,etime,args -p $(pgrep -f "[w]pe_offscreen_spike" | tr "\n" "," | sed "s/,$//") 2>/dev/null | head -6
[ "$(pgrep -f "[w]pe-webkit-2\\.0" | wc -l)" -gt 0 ] && ps -o pid,ppid,etime,args -p $(pgrep -f "[w]pe-webkit-2\\.0" | tr "\n" "," | sed "s/,$//") 2>/dev/null | head -6
true'
