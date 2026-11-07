export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
sshpass -e ssh -o StrictHostKeyChecking=no root@192.168.2.15 'sed -n "300,430p" /opt/wpe-sfos/libexec/atlantic/runtime-common.sh'
