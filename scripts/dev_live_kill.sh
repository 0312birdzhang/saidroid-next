export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
$SSH "pkill -f LiveProbe; sleep 1; pgrep -f LiveProbe >/dev/null && echo STILL || echo KILLED"
