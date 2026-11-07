#!/bin/bash
SSHPASS="${SSHPASS:?Set SSHPASS for device development}" sshpass -e ssh -o StrictHostKeyChecking=no root@bonito 'bash -s' <<'REMOTE'
export XDG_RUNTIME_DIR=/run/user/100000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket
su defaultuser -s /bin/sh -c 'export XDG_RUNTIME_DIR=/run/user/100000; export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket; gdbus introspect --session --dest org.nemomobile.lipstick --object-path / 2>&1 | grep -E "interface|method " | head -40' 2>&1
echo "=== private methods on / ==="
su defaultuser -s /bin/sh -c 'export XDG_RUNTIME_DIR=/run/user/100000; export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket; gdbus introspect --session --dest org.nemomobile.lipstick --object-path / --recurse 2>&1 | grep -iE "input|touch|tap|click" | head -20' 2>&1
REMOTE
