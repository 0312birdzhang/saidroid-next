#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SRC=/media/psf/Home/Documents/Codex/2026-07-08/zha/work/sailfish-bonito-port/tmp/saidroid-apks/QQ_9.3.50_arm64.apk
ls -l "$SRC" || exit 1
echo "=== 推到设备（大文件，慢慢来）==="
time sshpass -e scp -o StrictHostKeyChecking=no "$SRC" root@bonito:/home/art/realapps/qq.apk
$SSH "ls -l /home/art/realapps/qq.apk; df -h /home | tail -1"
