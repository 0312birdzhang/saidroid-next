#!/bin/sh
# Device state check. IMPORTANT: this script must ssh to the device -- a script run
# via `prlctl exec 'MeeGo Build' ...` executes inside the VM, so a bare `pgrep`
# inspects the VM, not Sailfish. (Learned the hard way: an empty "LIPSTICK=" line
# once made it look as if we had killed the compositor.)
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@192.168.2.15 '
echo "LOCK=$(cat /home/art/test/.device-lock/owner 2>/dev/null || echo FREE)"
echo "LIPSTICK=$(pgrep -f "$(echo bGlwc3RpY2s= | base64 -d)" | tr "\n" " ")"
echo "ATLANTIC=$(pgrep -f atlantic | tr "\n" " ")"
echo "WPEPROC=$(pgrep -f wpe-webkit | tr "\n" " ")"
echo "SPIKE=$(pgrep -f wpe_offscreen | tr "\n" " ")"
echo "SDBINDER=$(pgrep -f SdBinderRegistry | tr "\n" " ")"
echo "SDRUNTIME=$(pgrep -f SdRuntime | tr "\n" " ")"
echo "LOADAVG=$(cat /proc/loadavg)"
echo "DISPLAY_PROCS=$(ls /proc/*/comm 2>/dev/null | xargs -r cat 2>/dev/null | sort -u | grep -Ei "lipstick|compositor|topmost|invoker" | tr "\n" " ")"
'
