#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito"
L=/home/art/data/logs/com.tencent.mobileqq/20261027T044933-36648.log
$SSH "grep -n -i -E 'webview|WebView|QBrowser|MarginLayoutParams|NullPointer|LayoutParams' $L | head -60"
