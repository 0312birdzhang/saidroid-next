#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
$SSH "echo '--- wolfssl libs:'; ls -la /home/art/lib/libwolfssl* /usr/lib64/libwolfssl* 2>/dev/null | head; echo '--- wolfssl headers:'; ls /usr/include/wolfssl 2>/dev/null | head -3; echo '--- ca store:'; ls /home/art/etc/security/cacerts 2>/dev/null | head -3; ls /home/art/etc/security/cacerts 2>/dev/null | wc -l; echo '--- java wolfssl jar:'; ls -la /home/art/api29-root/java/dex/art/wolfssljni-hostdex.jar 2>/dev/null"
