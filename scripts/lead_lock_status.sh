#!/bin/bash
# Lead: read-only device lock + process state probe. Runs INSIDE the Parallels VM.
set -u
R=/media/psf/Home/WorkSpace/saidroid-next
echo "=== devlock status ==="
/bin/bash "$R/scripts/devlock.sh" status 2>&1
echo "=== owner file raw ==="
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH 'if [ -d /home/art/test/.device-lock ]; then ls -la /home/art/test/.device-lock/; echo -n "OWNER="; cat /home/art/test/.device-lock/owner; echo; else echo NO_LOCK_DIR; fi' 2>&1
echo "=== saildroid processes ==="
$SSH "pgrep -af 'saildroid|WPEWebProcess|WPENetworkProcess|wpe_offscreen' | head -20" 2>&1
echo "=== topmost ==="
$SSH "su defaultuser -c 'XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket gdbus call --session --dest org.nemomobile.lipstick --object-path / --method org.nemomobile.compositor.privateTopmostWindowProcessId'" 2>&1
