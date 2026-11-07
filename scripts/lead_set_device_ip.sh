#!/bin/bash
# 设备 DHCP 换 IP 后，把 VM 里的 bonito 主机名指到新地址。用法: bash lead_set_device_ip.sh 192.168.3.14
set -u
IP=${1:?usage: lead_set_device_ip.sh <ip>}
sed -i '/[[:space:]]bonito$/d' /etc/hosts
echo "$IP bonito" >> /etc/hosts
grep bonito /etc/hosts
getent hosts bonito
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 root@bonito 'echo SSH_OK_$(hostname); cut -d" " -f1 /proc/uptime'
