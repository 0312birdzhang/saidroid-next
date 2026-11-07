#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=6 root@bonito"
# 左侧边缘右滑 = 返回，退出相机
$SSH "/home/art/bin/sdinput swipe 2 1080 800 1080 250 25" 2>&1
sleep 2
$SSH "pidof jolla-camera || echo CAMERA_CLOSED" 2>&1
$SSH "python3 /home/art/bin/sdtool.py --package com.tencent.mobileqq shot pm-home2 2>&1" 2>&1
