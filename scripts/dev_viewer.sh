export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
echo "=== 找 sdview 和启动脚本 ==="
$SSH "ls -l /home/art/sdview 2>/dev/null; cat /home/art/render.sh 2>/dev/null | head -20"
