export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 'wc -l /opt/wpe-sfos/libexec/atlantic/runtime-common.sh; sed -n "1,140p" /opt/wpe-sfos/libexec/atlantic/runtime-common.sh'
