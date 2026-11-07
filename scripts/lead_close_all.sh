#!/bin/bash
# 关掉所有 owned SailDroid 进程（含 broker），deploy-component 的前置条件
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH 'for a in --manager --package=com.tencent.mobileqq --broker; do
  su - defaultuser -c "XDG_RUNTIME_DIR=/run/user/100000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/100000/dbus/user_bus_socket /home/art/bin/saildroid-open $a --close" 2>&1 | tail -1
done
sleep 2
echo OWNED_NOW:; pgrep -af "saildroid-supervisor|/home/art/api29-root|org.saildroid" | grep -v pgrep | head -5; echo END'
