#!/bin/bash
# VM side: push the RSS probe and read it back.
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
REPO=/media/psf/Home/WorkSpace/saidroid-next
H=root@bonito
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 $H"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=8"
$SSH "python3 /home/art/bin/sdtool.py --package org.example.saildroid.perfscroll close" >/dev/null 2>&1
$SCP -q "$REPO/scripts/perf/device-r80-rss.sh" "$H:/tmp/r80-rss.sh" || exit 5
$SSH "chmod 755 /tmp/r80-rss.sh && /tmp/r80-rss.sh" 2>&1
